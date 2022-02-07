import enum
from typing import Optional

import libcst


class Actions(enum.Enum):
    # we don't care about any of these values, just using them as sentinels
    DECORATOR_EVENT_CALLED = enum.auto()
    DECORATOR_LISTEN_NOT_CALLED = enum.auto()
    USING_SELF_ON_BOT_COMMAND = enum.auto()
    CLIENT_IS_NOT_BOT = enum.auto()
    PROCESS_COMMANDS_NOT_CALLED = enum.auto()


class BaseHelpTransformer(libcst.CSTTransformer):
    def __init__(self, find_all: bool = False):
        super().__init__()
        self.found_errors: list[Actions] = []
        self.find_all = find_all
        self.updates = {}

    def _check_code(self) -> bool:
        return bool(self.found_errors)

    def on_visit(self, node):
        if self.found_errors and not self.find_all:
            # don't visit anything else
            return False
        res = super().on_visit(node)
        if self.found_errors and not self.find_all:
            # don't visit anything else
            return False
        return res

    def on_leave(self, original_node, updated_node):
        if changes := self.updates.get(original_node):
            return changes(updated_node)
        return updated_node


class _FindCommandDecorator(libcst.CSTVisitor):
    def __init__(self):
        super().__init__()
        self.is_command_dec = False

    def visit_Decorator(self, node):
        if not isinstance(node.decorator, libcst.Call):
            return True
        func = node.decorator.func
        # find decorators that are like @thing.slash_command
        # but ensure to ignore @commands.command` since that should have self.`
        if func.attr.value.endswith("command") and func.value not in (
            "commands",
            "nextcord",
        ):
            self.is_command_dec = True
        return True


class EventListenerVisitor(BaseHelpTransformer):
    def visit_ClassDef(self, node: libcst.ClassDef):
        # don't check classdefs for decorators
        return False

    def visit_Decorator(self, node: libcst.Decorator) -> None:
        if (
            isinstance(node.decorator, libcst.Call)
            and node.decorator.func.attr.value == "event"
        ):
            self.found_errors.append(Actions.DECORATOR_EVENT_CALLED)
            # there's two solutions here. This needs to either be a listener or an event with no call.
            # this will be left up to implement later, for now, we convert it to just an uncalled event
            self.updates[node] = lambda node: node.with_changes(
                decorator=node.decorator.func
            )
        elif (
            isinstance(node.decorator, libcst.Attribute)
            and node.decorator.attr.value == "listen"
        ):
            self.found_errors.append(Actions.DECORATOR_LISTEN_NOT_CALLED)
            self.updates[node] = lambda node: node.with_changes(
                decorator=libcst.Call(node.decorator)
            )

    def visit_FunctionDef_params(self, node: libcst.FunctionDef) -> Optional[bool]:
        if not node.params or not node.decorators:
            return False
        first_param: libcst.Param = node.params.params[0]
        if not first_param.name.value == "self":
            return False
        # its self and a top level method, so check for a bot decorator
        # needs a decorator with `command` in the last section and to be called
        visitor = _FindCommandDecorator()
        node.visit(visitor)
        if visitor.is_command_dec:
            self.found_errors.append(Actions.USING_SELF_ON_BOT_COMMAND)

            def update(node: libcst.FunctionDef):
                params = node.params.with_changes(params=node.params.params[1:])
                return node.with_changes(params=params)

            self.updates[node] = update


class ClientIsNotBot(BaseHelpTransformer):

    BOT_CLASSES = ("Bot", "InteractionBot")
    def visit_Assign(self, node: libcst.Assign):
        # what
        if not isinstance(node.value, libcst.Call):
            return
        # search for client in the assign
        found_client = False
        possible_fix = lambda node: node
        for target in node.targets:
            if hasattr(target, "attr"):
                continue
            if target.target.value == "client":
                found_client = True

                def possible_fix(node: libcst.Assign):
                    targets = list([t for t in node.targets])
                    pos = targets.index(target)

                    targets.pop(pos)

                    targets.insert(
                        pos,
                        libcst.AssignTarget(
                            target=target.target.with_changes(value="bot")
                        ),
                    )
                    return node.with_changes(targets=targets)

                break

        if not found_client:
            return
        # search for bot in the class assigment
        found_bot = False

        # get the last call
        func = node.value.func
        if isinstance(func, libcst.Name):
            if func.value in self.BOT_CLASSES:
                found_bot = True

        elif isinstance(func, libcst.Attribute):
            if func.attr.value in self.BOT_CLASSES:
                found_bot = True

        if not found_bot:
            return

        self.found_errors.append(Actions.CLIENT_IS_NOT_BOT)
        return
        self.updates[node] = possible_fix


class _FindProcessCommands(libcst.CSTTransformer):
    def __init__(self):
        self.found_process_commands = False

    def visit_Expr(self, node: libcst.Expr):
        if not isinstance(node.value, libcst.Await):
            return
        if not isinstance(node.value.expression, libcst.Call):
            return
        expr = node.value.expression
        if not hasattr(expr, "func"):
            return
        if not isinstance(expr.func, libcst.Attribute):
            return

        name = expr.func.attr.value
        if name == "process_commands":
            self.found_process_commands = True
            return True


class ProcessCommandsTransformer(BaseHelpTransformer):
    def visit_FunctionDef(self, node: libcst.FunctionDef):
        if not node.decorators:
            return
        # check for name on_message
        if node.name.value != "on_message":
            return
        if not node.params.params:
            # no params so different error, don't handle it right now
            return
        is_event = False
        for decorator in node.decorators:
            if isinstance(decorator.decorator, libcst.Call):
                continue
            if not isinstance(decorator.decorator, libcst.Attribute):
                continue

            attr = decorator.decorator

            name = attr.attr.value

            if name == "event":
                # get the bot name
                bot_instance = attr.value.value

                is_event = True
                break

        if not is_event:
            return

        # now we need to visit the body and look for a call to process_commands
        visitor = _FindProcessCommands()
        node.body.visit(visitor)
        if visitor.found_process_commands:
            return

        self.found_errors.append(Actions.PROCESS_COMMANDS_NOT_CALLED)

        def update(node: libcst.FunctionDef):
            params = list(node.params.params)
            message_param_name = params[0].name.value
            body = list(node.body.body)

            body.append(
                libcst.SimpleStatementLine(
                    [
                        libcst.Expr(
                            libcst.Await(
                                libcst.Call(
                                    libcst.Attribute(
                                        libcst.Name(bot_instance),
                                        libcst.Name("process_commands"),
                                    ),
                                    args=[libcst.Arg(libcst.Name(message_param_name))],
                                )
                            )
                        )
                    ]
                )
            )
            body = node.body.with_changes(body=body)
            return node.with_changes(body=body)

        self.updates[node] = update
