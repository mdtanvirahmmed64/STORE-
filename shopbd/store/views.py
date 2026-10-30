from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from core.utils import safe_redirect

from .forms import ReviewForm
from .models import Brand, Category, Product, Review, Wishlist

SORT_OPTIONS = {
    "newest": (_lazy("Newest"), "-created_at"),
    "price_low": (_lazy("Price: Low to High"), "effective_price"),
    "price_high": (_lazy("Price: High to Low"), "-effective_price"),
    "popular": (_lazy("Best Selling"), "-sold_count"),
    "rating": (_lazy("Top Rated"), "-rating"),
}


def _decimal(value):
    try:
        return Decimal(value) if value not in (None, "") else None
    except InvalidOperation:
        return None


def product_list(request, slug=None):
    from django.db.models import Case, When, DecimalField

    products = Product.objects.active().select_related("brand", "category").prefetch_related("variations", "translations")
    category = None
    if slug:
        category = get_object_or_404(Category.objects.prefetch_related("translations"), slug=slug, is_active=True)
    elif request.GET.get("category"):
        category = Category.objects.filter(slug=request.GET["category"], is_active=True).first()
    if category:
        products = products.filter(category_id__in=category.get_descendant_ids())

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(short_description__icontains=q) | Q(sku__iexact=q)
            | Q(brand__name__icontains=q) | Q(category__name__icontains=q)
            | Q(translations__name__icontains=q) | Q(category__translations__name__icontains=q)
        ).distinct()

    selected_brands = request.GET.getlist("brand")
    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    # price filter works on the final (discounted) price
    products = products.annotate(effective_price=Case(
        When(discount_price__isnull=False, discount_price__lt=F("price"), then=F("discount_price")),
        default=F("price"), output_field=DecimalField(max_digits=10, decimal_places=2),
    ))
    min_price, max_price = _decimal(request.GET.get("min_price")), _decimal(request.GET.get("max_price"))
    if min_price is not None:
        products = products.filter(effective_price__gte=min_price)
    if max_price is not None:
        products = products.filter(effective_price__lte=max_price)

    if request.GET.get("rating"):
        products = products.filter(rating__gte=_decimal(request.GET["rating"]) or 0)
    if request.GET.get("in_stock"):
        products = products.filter(stock__gt=0)
    if request.GET.get("discount"):
        products = products.filter(discount_price__isnull=False, discount_price__lt=F("price"))
    flag = request.GET.get("filter")
    if flag == "flash":
        products = products.filter(is_flash_sale=True)
    elif flag == "featured":
        products = products.filter(is_featured=True)
    elif flag == "new":
        products = products.filter(is_new_arrival=True)

    sort = request.GET.get("sort", "newest")
    products = products.order_by(SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"])[1], "-id")

    page_obj = Paginator(products, 20).get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    brand_qs = Brand.objects.filter(is_active=True)
    if category:
        brand_qs = brand_qs.filter(products__category_id__in=category.get_descendant_ids()).distinct()

    context = {
        "category": category,
        "subcategories": (category.children.filter(is_active=True) if category else
                          Category.objects.filter(parent__isnull=True, is_active=True)).prefetch_related("translations"),
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "brands": brand_qs,
        "selected_brands": selected_brands,
        "sort": sort,
        "sort_options": {k: v[0] for k, v in SORT_OPTIONS.items()},
        "q": q,
        "querystring": params.urlencode(),
        "total": page_obj.paginator.count,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.active().select_related("category__parent", "brand").prefetch_related(
            "images", "variations", "translations", "category__translations", "category__parent__translations"),
        slug=slug,
    )
    Product.objects.filter(pk=product.pk).update(views=F("views") + 1)

    variations = {}
    for v in product.variations.all():
        if v.is_active:
            variations.setdefault(v.kind, {"label": v.get_kind_display(), "options": []})["options"].append(v)

    related = (Product.objects.active().filter(category=product.category)
               .exclude(pk=product.pk).prefetch_related("variations", "translations").order_by("-sold_count")[:10])
    reviews = product.reviews.filter(is_approved=True).select_related("user")

    user_review, can_review, in_wishlist = None, False, False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        can_review = user_review is None
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    # rating breakdown for the bar chart (5★ → 1★)
    total_reviews = reviews.count()
    breakdown = []
    for star in range(5, 0, -1):
        n = reviews.filter(rating=star).count()
        breakdown.append((star, n, int(n * 100 / total_reviews) if total_reviews else 0))

    context = {
        "product": product,
        "variations": variations,
        "related": related,
        "reviews": reviews[:20],
        "breakdown": breakdown,
        "review_form": ReviewForm(),
        "can_review": can_review,
        "in_wishlist": in_wishlist,
    }
    return render(request, "store/product_detail.html", context)


@login_required
@require_POST
def add_review(request, slug):
    product = get_object_or_404(Product.objects.active(), slug=slug)
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, _("You have already reviewed this product."))
        return redirect(product.get_absolute_url())
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, _("Thank you for your review!"))
    else:
        messages.error(request, _("Please give a rating and write a comment."))
    return redirect(product.get_absolute_url() + "#reviews")


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product").prefetch_related(
        "product__variations", "product__translations")
    return render(request, "store/wishlist.html", {"items": items})


@require_POST
def wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "login_required": True, "message": _("Please login first.")}, status=401)
        return redirect("accounts:login")
    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
    count = Wishlist.objects.filter(user=request.user).count()
    msg = _("Added to wishlist.") if created else _("Removed from wishlist.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "added": created, "message": msg, "wishlist_count": count})
    messages.success(request, msg)
    return safe_redirect(request, request.POST.get("next"), product.get_absolute_url())


def search_suggest(request):
    q = request.GET.get("q", "").strip()
    results = []
    if len(q) >= 2:
        for p in Product.objects.active().filter(Q(name__icontains=q) | Q(translations__name__icontains=q)).distinct().prefetch_related("translations")[:8]:
            results.append({
                "name": p.tr("name"),
                "url": p.get_absolute_url(),
                "price": f"{p.final_price:,.0f}",
                "image": p.image.url if p.image else "",
            })
    return JsonResponse({"results": results})
