from django import forms
from django.utils.html import mark_safe


class JRangeWidget(forms.widgets.Input):

    def format_output(self, rendered_widgets):
        # Method was removed in Django 1.11.
        return '-'.join(rendered_widgets)

    def render(self, name, value, attrs=None):
        attrs['class'] = name
        jrange_script = "\
            <script type='text/javascript'>\
            var max_value = $('.{0}').attr('max').match(/\d+/);\
            $('.{0}').jRange({{\
                from: 0,\
                to: max_value,\
                step: 1,\
                width: 240,\
                format: '%s',\
                showLabels: true,\
                isRange : true,\
                theme: 'theme-blue'\
            }});\
            $('.{0}').jRange('setValue', $('.{0}').attr('value'));\
            </script>\
        ".format(name)
        html = super(JRangeWidget, self).render(name, value, attrs)
        html = '%s%s' % (html, jrange_script)
        return html

    def decompress(self, value):
        if value:
            value = value.split(',')
        else:
            value = [None, None]
        return value
