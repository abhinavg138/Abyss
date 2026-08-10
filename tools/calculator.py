from tools.base import BaseTool

class CalculatorTool(BaseTool):

    def execute(self, expression):

        return eval(expression)