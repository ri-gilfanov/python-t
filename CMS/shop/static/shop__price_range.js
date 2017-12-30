var max_price = $('#id_price_1').attr('max').match(/\d+/);
var price_0 = $('#id_price_0').attr('value').match(/\d+/);
var price_1 = $('#id_price_1').attr('value').match(/\d+/);
// $(".product_filter *:nth-child(3)").hide();

function xxxx() {
    var value_range_string = $('.price_range').attr('value');
    var value_range_list = value_range_string.split(',');
    $('#id_price_0').attr('value', Math.min(value_range_list[0], value_range_list[1]));
    $('#id_price_1').attr('value', Math.max(value_range_list[0], value_range_list[1]));
};

$('.price_range').jRange({
    from: 0,
    to: max_price,
    step: 1,
    format: '%s',
    width: 260,
    showLabels: true,
    isRange : true,
    onstatechange: xxxx,
    theme: 'theme-blue'
});



$('.price_range').jRange('setValue', [price_0, price_1].join());
