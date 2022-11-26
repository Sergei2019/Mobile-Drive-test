from collections import namedtuple

Kpi = namedtuple(
    "Kpi", ["pos", "color", "range_min", "range_max",]
)


RSRP_ = (
    Kpi(0, "#B30000", float("-inf"), -120,),
    Kpi(1, "#FF0000", -120, -110,),
    Kpi(2, "#FFFF00", -110, -100,),
    Kpi(3, "#00FF00", -100, -90,),
    Kpi(4, "#008000", -90, float("+inf"),),
)

RSRQ_ = (
    Kpi(0, "#B30000", float("-inf"), -15,),
    Kpi(1, "#FF0000", -15, -13,),
    Kpi(2, "#FFFF00", -13, -11,),
    Kpi(3, "#00FF00", -11, -9,),
    Kpi(4, "#008000", -9, float("+inf"),),
)

RSRP_BP = (
    Kpi(0, "#000000", float("-inf"), -120,),
    Kpi(1, "#FF0000", -120, -113,),
    Kpi(2, "#FFFF00", -113, -105,),
    Kpi(3, "#008000", -105, float("+inf"),),
)

MEAS_BP = (
    Kpi(0, "#B30000", 300, float("+inf")),
    Kpi(1, "#FFFF00", 150, 300,),
    Kpi(2, "#008000", 75, 150,),
    Kpi(3, "#808080", 0, 75,),
)


