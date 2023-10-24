from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status
from rest_framework.response import Response
from recipes.models import (
    Ingredient,
    Favorite,
    ShoppingCart,
    Recipe,
    RecipeIngredient,
    Tag,
)
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .permissions import ReadOnly, IsAdmin, IsAuthor
from .serializers import (
    FoodUserSerializer,
    IngredientSerializer,
    SubscriptionSerializer,
    TagSerializer,
    RecipeCreateSerializer,
    RecipeCutFieldsSerializer,
    RecipeSerializer,
)
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

from foodgram_project.settings import (
    START,
    BIG_FONT,
    SMALL_FONT,
    BIG_FONT_SIZE,
    SMALL_FONT_SIZE,
    COLUMN_0,
    COLUMN_1,
    LINE_0,
    LINE_1,
    TEXT_0,
    NEXT_LINE)
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    AllowAny
)


class FoodUserViewSet(UserViewSet):
    # permission_classes = (ReadOnly,)

    @action(
        detail=False,
        permission_classes=(IsAuthor | IsAdmin,))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        serializer = SubscriptionSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete',),
        permission_classes=(IsAuthor | IsAdmin,))
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        user = request.user
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                author,
                data=request.data,
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED)
        try:
            subscription = Subscription.objects.get(user=user, author=author)
        except ObjectDoesNotExist:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST,)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    filterset_class = RecipeFilter
    permission_classes = (ReadOnly | IsAuthor | IsAdmin,)

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredient__ingredient', 'tags',
        ).all()
        return recipes

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        if self.action in ('favorite', 'shopping_cart',):
            return RecipeCutFieldsSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe(self, user, recipe, model):
        try:
            model.objects.create(user=user, recipe=recipe)
        except IntegrityError:
            return Response(
                {'errors': 'Этот рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(
            self.get_serializer(recipe).data,
            status=status.HTTP_201_CREATED)

    def delete_recipe(self, user, recipe, model):
        try:
            state = model.objects.get(user=user, recipe=recipe)
        except ObjectDoesNotExist:
            return Response(
                {'errors': 'Что мертво умереть не может'},
                status=status.HTTP_400_BAD_REQUEST,)
        state.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def make_doc(self, buffer, ingredients, INGREDIENT, AMOUNT, UNIT):
        doc = canvas.Canvas(buffer)
        doc.setFont(BIG_FONT, BIG_FONT_SIZE)
        doc.drawString(COLUMN_0, LINE_0, TEXT_0)
        doc.setFont(SMALL_FONT, SMALL_FONT_SIZE)
        y = LINE_1
        for item in ingredients:
            doc.drawString(COLUMN_0, y, f'- {item[INGREDIENT]}',)
            doc.drawString(COLUMN_1, y, f'{str(item[AMOUNT])} {item[UNIT]}',)
            y -= NEXT_LINE
        doc.showPage()
        doc.save()

    @action(
        detail=True,
        methods=('post', 'delete'))
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe(user, recipe, Favorite)
        return self.delete_recipe(user, recipe, Favorite)

    @action(
        detail=True,
        methods=('post', 'delete'))
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe(user, recipe, ShoppingCart)
        return self.delete_recipe(user, recipe, ShoppingCart)

    @action(
        detail=False)
    def download_shopping_cart(self, request):
        INGREDIENT = 'ingredient__name'
        UNIT = 'ingredient__measurement_unit'
        AMOUNT = 'amount'

        user = request.user
        if not user.shoppingcart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).values(INGREDIENT, UNIT,).annotate(amount=Sum(AMOUNT))
        buffer = io.BytesIO()
        self.make_doc(buffer, ingredients, INGREDIENT, AMOUNT, UNIT)
        buffer.seek(START)
        return FileResponse(
            buffer, as_attachment=True, filename='Shopping-list.pdf')


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (ReadOnly | IsAdmin,)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (ReadOnly | IsAuthor | IsAdmin,)
