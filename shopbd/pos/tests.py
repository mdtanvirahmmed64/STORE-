"""POS / multi-branch tests.  Run with:  python manage.py test"""
import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import SiteSetting
from store.models import Category, Product

from .models import Branch, BranchStaff, BranchStock, Sale, StockTransfer


class POSTests(TestCase):
    def setUp(self):
        SiteSetting.load()
        cat = Category.objects.create(name="Grocery")
        self.p = Product.objects.create(name="Rice 5kg", category=cat, price=Decimal("500"), stock=50,
                                        sku="RICE5", image="products/x.jpg")
        self.dhn = Branch.objects.create(name="Dhanmondi", code="dhn")
        self.utt = Branch.objects.create(name="Uttara", code="UTT")
        BranchStock.objects.create(branch=self.dhn, product=self.p, quantity=10)
        BranchStock.objects.create(branch=self.utt, product=self.p, quantity=3)
        self.cashier = User.objects.create_user("cash", "c@x.com", "pass12345")
        BranchStaff.objects.create(user=self.cashier, branch=self.dhn, role="cashier", max_discount_percent=10)
        self.manager = User.objects.create_user("man", "m@x.com", "pass12345")
        BranchStaff.objects.create(user=self.manager, branch=self.dhn, role="manager")
        self.customer = User.objects.create_user("cust", "u@x.com", "pass12345")

    def sell(self, branch=None, qty=2, **extra):
        body = {"branch": (branch or self.dhn).pk, "items": [{"product_id": self.p.pk, "quantity": qty}],
                "payment_method": "cash", "paid_amount": "5000", **extra}
        return self.client.post(reverse("pos:create_sale"), json.dumps(body), content_type="application/json")

    def qty(self, branch):
        return BranchStock.objects.get(branch=branch, product=self.p).quantity

    def test_code_is_uppercase(self):
        self.assertEqual(self.dhn.code, "DHN")

    def test_sale_creates_receipt_and_deducts_branch_stock(self):
        self.client.login(username="cash", password="pass12345")
        r = self.sell(qty=2).json()
        self.assertTrue(r["ok"], r)
        sale = Sale.objects.get()
        self.assertEqual(sale.total, Decimal("1000"))
        self.assertEqual(sale.change_amount, Decimal("4000"))
        self.assertTrue(sale.number.startswith("DHN-"))
        self.assertEqual(self.qty(self.dhn), 8)
        self.assertEqual(self.qty(self.utt), 3)          # other branch untouched
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 50)               # online stock untouched
        page = self.client.get(reverse("pos:receipt", args=[sale.number]))
        self.assertContains(page, sale.number)
        self.assertContains(page, "Rice 5kg")

    def test_not_enough_stock(self):
        self.client.login(username="cash", password="pass12345")
        r = self.sell(qty=11)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(self.qty(self.dhn), 10)

    def test_cashier_cannot_sell_from_other_branch(self):
        self.client.login(username="cash", password="pass12345")
        self.assertEqual(self.sell(branch=self.utt).status_code, 403)

    def test_discount_limit(self):
        self.client.login(username="cash", password="pass12345")
        self.assertEqual(self.sell(discount_type="percent", discount_value="50").status_code, 400)
        self.assertTrue(self.sell(discount_type="percent", discount_value="10").json()["ok"])
        self.assertEqual(Sale.objects.get().total, Decimal("900"))
        # a manager has no limit
        self.client.login(username="man", password="pass12345")
        self.assertTrue(self.sell(qty=1, discount_type="amount", discount_value="250").json()["ok"])

    def test_cash_paid_less_than_total(self):
        self.client.login(username="cash", password="pass12345")
        self.assertEqual(self.sell(paid_amount="10").status_code, 400)

    def test_customer_has_no_pos_access(self):
        self.client.login(username="cust", password="pass12345")
        self.assertIn(self.client.get(reverse("pos:terminal")).status_code, (302, 403))
        self.assertNotEqual(self.sell().status_code, 200)

    def test_return_is_manager_only_and_restocks(self):
        self.client.login(username="cash", password="pass12345")
        number = self.sell(qty=4).json()["number"]
        self.assertEqual(self.qty(self.dhn), 6)
        self.assertEqual(self.client.post(reverse("pos:sale_return", args=[number])).status_code, 403)
        self.assertEqual(self.client.get(reverse("pos:dashboard")).status_code, 403)
        self.client.login(username="man", password="pass12345")
        self.client.post(reverse("pos:sale_return", args=[number]))
        self.assertEqual(Sale.objects.get().status, "returned")
        self.assertEqual(self.qty(self.dhn), 10)
        self.assertEqual(self.client.get(reverse("pos:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("pos:sales")).status_code, 200)

    def test_stock_transfer(self):
        StockTransfer.objects.create(from_branch=None, to_branch=self.utt, product=self.p, quantity=5)
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 45)
        self.assertEqual(self.qty(self.utt), 8)
        StockTransfer.objects.create(from_branch=self.dhn, to_branch=self.utt, product=self.p, quantity=2)
        self.assertEqual(self.qty(self.dhn), 8)
        self.assertEqual(self.qty(self.utt), 10)

    def test_superuser_sees_all_branches(self):
        User.objects.create_superuser("boss", "b@x.com", "pass12345")
        self.client.login(username="boss", password="pass12345")
        r = self.client.get(reverse("pos:dashboard"))
        self.assertContains(r, "Dhanmondi")
        self.assertContains(r, "Uttara")
        self.assertEqual(self.sell(branch=self.utt, qty=1).status_code, 200)
