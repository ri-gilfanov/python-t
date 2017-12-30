var url = "/request_to_cart/";

function cart__error() {
    alert('Ошибка. Проверьте соединение.')
};

function cart__change_score(difference) {
    var score = parseInt($('#cart__score').text().match(/\d+/));
    if (isNaN(score) == true) {score = 0};
    score += difference;
    if (score > 0) {$('#cart__score').text("Товаров в корзине " + score)}
    else {$('#cart__score').text("Корзина пока пуста")};
};

function cart__set_product(element) {
    var pk = parseInt($(element).attr('id').match(/\d+/));
    $.ajax({
        type: "POST",
        url: url,
        data: {"method": "cart__set_product", "pk": pk},
        success: function() {
            $( element ).html('<span class="fa fa-cart-arrow-down"></span><span>&nbsp;удалить</span>');
            $( element ).attr('onclick', 'cart__unset_product(this)');
            $( element ).addClass('btn__dark_sel');
            $( '#cart__table_tr_' + pk + ' td:not(:last-child)' ).css({ opacity: "1" });
            cart__change_score(1);
            $('#cart__quantity_'+pk).val(1);
        },
        error: cart__error
    });
    return false;
};

function cart__unset_product(element) {
    var pk = parseInt($(element).attr('id').match(/\d+/));
    $.ajax({
        type: "POST",
        url: url,
        data: {"method": "cart__unset_product", "pk": pk},
        success: function() {
            $( element ).html('<span class="fa fa-cart-plus"></span><span>&nbsp;добавить</span>');
            $( element ).attr('onclick', 'cart__set_product(this)');
            $( element ).removeClass('btn__dark_sel');
            $( '#cart__table_tr_' + pk + ' td:not(:last-child)' ).css({ opacity: "0.5" });
            cart__change_score(-1);
            $('#cart__quantity_'+pk).val(1);
        },
        error: cart__error
    });
    return false;
};

function cart__clear_cart() {
    $.ajax({
        type: "POST",
        url: url,
        data: {"method": "cart__clear_cart"},
        success: function() {},
        error: cart__error
    });
    return false;
};






function cart__change_quantity(element) {
    var pk = parseInt($(element).attr('id').match(/\d+/));
    cart__set_quantity(pk);
};


function cart__set_quantity(pk, difference) {
    var quantity_input = $('#cart__quantity_'+pk)
    var quantity = parseInt(quantity_input.val());
    if (isNaN(difference) == true) {difference = 0};
    if (isNaN(quantity) == true) {quantity = 1};
    quantity += difference;
    if (quantity < 1) {quantity = 1};
    quantity_input.val(quantity);
    $.ajax({
        type: "POST",
        url: url,
        data: {"method": "cart__set_product", "pk": pk, "quantity": quantity},
        success: function() {},
        error: cart__error
    });
    return false;
};

function cart__inc_quantity(element) {
    var pk = parseInt($(element).attr('id').match(/\d+/));
    cart__set_quantity(pk, 1);
    return false;
};

function cart__dec_quantity(element) {
    var pk = parseInt($(element).attr('id').match(/\d+/));
    cart__set_quantity(pk, -1);
    return false;
};
