
import pyparsing as pp

import builtins
import collections
import functools
import typing

__all__ = ['annotation_parser']


def parser(func):
    @functools.wraps(func)
    @functools.lru_cache(None)
    def wrapper(*args, **kwargs):
        expr = func(*args, **kwargs)
        
        def parse(text):
            try:
                return expr.parseString(text, parseAll=True)[0]
            except pp.ParseException:
                raise SyntaxError from None
        
        return parse
    
    return wrapper


def delimited_list(expr, sep=',', *, allow_empty=False, allow_whitespace=True, type_=tuple):
    if isinstance(sep, str):
        sep = pp.Literal(sep)
    
    if allow_whitespace:
        e = expr
    else:
        sep = sep.copy().leaveWhitespace()
        e = expr.copy().leaveWhitespace()
    
    if allow_empty:
        expr = pp.Optional(expr)
    
    list_expr = expr + pp.ZeroOrMore(pp.Suppress(sep) + e)
    list_expr = list_expr.setParseAction(lambda s, loc, toks: [type_(toks)])
    return list_expr


@parser
def annotation_parser(module):
    CONVENIENCE_NAMES = {
        'typing': typing,
        'dictionary': dict,
        'text': str,
        'integer': int,
        'boolean': bool,
        'range object': range,
        'class': type,
        'metaclass': typing.Callable[[str, typing.Tuple[type], dict], type],
    }
    # Using a ChainMap lets us see the module's current dict, even
    # if the parser was generated and cached a long time ago
    SCOPE = collections.ChainMap(
        CONVENIENCE_NAMES,
        vars(builtins),
        vars(typing),
    )
    
    if module is not None:
        if isinstance(module, str):
            module = sys.modules[module]
        
        SCOPE.update(vars(module))

    def parse_identifier(s, loc, toks):
        name, *attrs = toks
        
        try:
            value = SCOPE[name]
        except KeyError:
            raise NameError('Unknown name {!r} in annotation'.format(name))
        
        for attr in attrs:
            value = getattr(value, attr)
        
        return value

    def parse_subscript(s, loc, toks):
        container, key = toks
        return container[key]
    
    name = pp.Word(pp.alphas + '_', pp.alphanums + '_')

    identifier = delimited_list(name, '.', allow_whitespace=False)
    identifier = identifier.setParseAction(parse_identifier)

    ellipsis = pp.Keyword('...').setParseAction(lambda: ...)
    none = pp.Keyword('None').setParseAction(lambda: [None])  # None is a special value and must be enclosed in a list
    builtin_constant = ellipsis | none

    expr = pp.Forward()

    list_ = pp.Suppress('[') + delimited_list(expr, allow_empty=True, type_=list) + pp.Suppress(']')

    simple_value = builtin_constant | identifier | list_

    subscript_value = simple_value + pp.Suppress('[') + delimited_list(expr) + pp.Suppress(']')
    subscript_value = subscript_value.setParseAction(parse_subscript)

    expr <<= subscript_value | simple_value
    
    return expr


@parser
def parameter_parser(module=None):
    def parse_param(s, loc, toks):
        kwargs = {
            'name': toks['name']
        }
        
        for key in ('annotation', 'default'):
            if key in toks:
                kwargs[key] = toks[key]
        
        return kwargs
    
    annotation = annotation_parser(module)
    
    name = pp.Word(pp.alphas + '_', pp.alphanums + '_')
    
    int_ = pp.Word(pp.nums)
    float_ = int_ + pp.Literal('.').leaveWhitespace() + int_
    int_or_float = float_ | int_
    complex_ = pp.Optional(pp.Optional(int_or_float) + pp.OneOf('+-')) + int_or_float + pp.Literal('j').leaveWhitespace()
    number = pp.Optional('-') + (complex_ | int_or_float)
    
    string = pp.Regex(r"""b?(['"])([^\\]|\\.)*\1""")
    value = string | number
    
    param = name('name') + pp.Optional(pp.Suppress(':') + annotation('annotation')) + pp.Optional(pp.Suppress('=') + value('default'))
    param = param.setParseAction(parse_param)
    
    return param


@parser
def param_list_parser(module=None):
    param = parameter_parser(module)
    
    another_param = ',' + param | ',' + pp.Literal('[') + para
    another_
    
    param_list = param + pp.Optional(',' + param_list)
    
    param_list = param + pp.ZeroOrMore(another_param)
    
    parser = pp.Optional('[' + param_list + ']' | param_list)
    return parser
