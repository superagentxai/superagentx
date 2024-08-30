import pandas
import webbrowser
import os

from enum import Enum
from math import pi
from bokeh.plotting import figure, output_file, show
from bokeh.models import FactorRange
from bokeh.palettes import Category20c
from bokeh.transform import cumsum

from agentx.visualization.exceptions import InvalidChartType


class ChartType(str, Enum):
    LINE = 'line'
    VBAR = 'vbar'
    HBAR = 'hbar'
    PIE = 'pie'
    TABLE = 'table'


class Visualize:

    def render_charts(
            self,
            chart_type: str | Enum,
            data: dict | list
    ):
        output_file("agentx_chart_output.html")

        match chart_type.lower():
            case ChartType.LINE:
                self.line_chart(data)
            case ChartType.VBAR:
                self.verticalBar(data)
            case ChartType.HBAR:
                self.horizontalBar(data)
            case ChartType.PIE:
                self.pieChart(data)
            case ChartType.TABLE:
                self.table_chart(data)
            case _:
                raise InvalidChartType(f'Invalid chart type `{chart_type}`')

    @staticmethod
    def line_chart(
            data: dict | list,
            title: str = "Line Chart",
            line_width: int = 2,
            color: str = "#1890ff"
    ):
        if isinstance(data, dict):
            data = [data]

        for items in data:
            x = items["x"]
            y = items["y"]

            chart = figure(
                title=title,
                x_axis_label="x",
                y_axis_label="y",
                outer_width=400,
                outer_height=400
            )
            chart.line(
                x,
                y,
                line_width=line_width,
                color=color
            )
            show(chart)

    @staticmethod
    def verticalBar(
            data: dict | list,
            title: str = "VerticalBar Chart",
            width: float = 0.7,
            color: str = "#1890ff"
    ):
        if isinstance(data, dict):
            data = [data]
        print(len(data))
        for items in data:
            x = list(items.keys())
            top = list(items.values())

            chart = figure(
                x_range=x,
                title=title
            )
            chart.vbar(
                x=x,
                top=top,
                width=width,
                color=color
            )
            show(chart)

    @staticmethod
    def horizontalBar(
            data: dict | list,
            title: str = "HorizontalBar Chart",
            color: str = "#1890ff",
            height: float = 0.7,
    ):
        if isinstance(data, dict):
            data = [data]

        for items in data:
            x = list(items.keys())
            right = list(items.values())

            chart = figure(
                y_range=FactorRange(factors=x),
                title=title
            )
            chart.hbar(
                y=x,
                right=right,
                height=height,
                color=color
            )
            show(chart)

    @staticmethod
    def pieChart(
            data: dict | list,
            title: str = "Pie Chart",
            line_color: str = "white",
            fill_color: str = "color",
    ):
        if isinstance(data, dict):
            data = [data]

        for items in data:
            data = pandas.Series(items).reset_index(name='value').rename(columns={'index': 'key'})
            data['angle'] = data['value'] / data['value'].sum() * 2 * pi
            data['color'] = Category20c[len(items)]
            chart = figure(
                title=title,
                tools="hover",
                toolbar_location=None,
                tooltips="@key:@value",
                x_range=(-0.5, 1.0)
            )
            chart.wedge(
                x=0,
                y=0,
                radius=0.4,
                start_angle=cumsum('angle', include_zero=True),
                end_angle=cumsum('angle'),
                line_color=line_color,
                fill_color=fill_color,
                legend_field="key",
                source=data
            )
            chart.axis.axis_label = None
            chart.axis.visible = False
            chart.grid.grid_line_color = None
            show(chart)

    @staticmethod
    def table_chart(
            data: dict | list
    ):
        if isinstance(data, dict):
            data = [data]

        table_data = pandas.DataFrame(data)
        output_file = "agentx_table.html"
        table_data.to_html(output_file)
        filename = 'file:///' + os.getcwd() + '/' + output_file
        webbrowser.open_new_tab(filename)
