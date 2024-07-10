def spec(HAPPY=0, SAD=0):
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 720,
        "height": 200,
        "data": {
            "values": [
                {"color": "#d73030", "count": SAD, "label": "sad"},
                {"color": "#77b895", "count": HAPPY, "label": "happy"},
            ]
        },
        "mark": {"type": "bar", "width": {"band": 0.9}, "fontSize": 10},
        "encoding": {
            "x": {
                "axis": {"labelFontSize": 14, "labelAngle": 0, "title": ""},
                "field": "label",
                "type": "nominal",
            },
            "y": {
                "axis": {"labelFontSize": 14, "labelAngle": 0, "title": ""},
                "field": "count",
                "type": "quantitative",
            },
            "color": {"field": "color", "type": "nominal", "scale": None},
        },
    }
