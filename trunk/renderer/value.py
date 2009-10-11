class ValueRenderer(object):
    """
    Returns the main value as a string.
    """

    key = 'value'
    select = 'value'
    serie = None

    def __init__(self, key='value', select='value', serie=None):
        self.select = select
        self.serie = serie
        self.key = key

    def render(self,data,context={}):
        if self.select == "last":
            return data['series'][self.serie][len(data['series'][self.serie])-1]
        else:
            if self.select == "value":
                return data[self.key]
