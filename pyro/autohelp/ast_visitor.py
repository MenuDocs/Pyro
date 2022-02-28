import enum
from typing import Optional

import libcst


class Actions(enum.IntFlag):
    # we don't care about any of these values being specific, as long as they're consistent per run
    # we use them for caching and determining how to handle the error
    DECORATOR_EVENT_CALLED = enum.auto()
    DECORATOR_LISTEN_NOT_CALLED = enum.auto()
    USING_SELF_ON_BOT_COMMAND = enum.auto()
    CLIENT_IS_NOT_BOT = enum.auto()
    PROCESS_COMMANDS_NOT_CALLED = enum.auto()
    MISSING_SELF_IN_EVENT_OR_COMMAND = enum.auto()
    INCORRECT_CTX_TYPEHINT = enum.auto()
    INCORRECT_INTERACTION_TYPEHINT = enum.auto()
    USED_PASS_CONTEXT = enum.auto()


class BaseHelpTransformer(libcst.CSTTransformer):
    """Base Help Transformer which modifies nodes based on update methods and stores a list of found errors."""

    def __init__(self, find_all: bool = False):
        super().__init__()
        self.found_errors: list[Actions] = []
        self.find_all = find_all
        self.updates = {}

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


class _FindNeedsSelfDecorator(libcst.CSTVisitor):
    """Find a method that requires a self argument based on the decorators."""

    def __init__(self):
        super().__init__()
        self.has_deco = False
        self.needs_self = False
        self.deco: Optional[str] = None

    def visit_Decorator(self, node):
        if isinstance(node.decorator, libcst.Call):
            root = node.decorator.func.value.value
            meth = node.decorator.func.attr.value
        elif isinstance(node.decorator, libcst.Attribute):
            root = node.decorator.attr.value
            meth = node.decorator.value.value
        else:
            return
        # find decorators that are like @thing.slash_command
        # but ensure to ignore @commands.command` since that should have self.`
        if meth in ("event", "group") or meth.endswith("command"):
            self.has_deco = True
            if root in ("commands", "nextcord"):
                self.needs_self = True

            self.deco: str = meth
            return True


class EventListenerVisitor(BaseHelpTransformer):
    """Listeners and events should not have a self argument when not part of a class definition.

    Eg, bot.listen and bot.event should not have a self argument.
    """

    def __init__(self, find_all: bool = True):
        super().__init__(find_all)

    def visit_ClassDef(self, node: libcst.ClassDef):
        # don't check classdefs for decorators
        return False

    def visit_Decorator(self, node: libcst.Decorator) -> None:
        if (
            isinstance(node.decorator, libcst.Call)
            and node.decorator.func.attr.value == "event"
        ):
            self.found_errors.append(Actions.DECORATOR_EVENT_CALLED)
            # switch the event to not be called
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
        if not node.params.params or not node.decorators:
            return False
        first_param: libcst.Param = node.params.params[0]
        if not first_param.name.value == "self":
            return False
        # its self and a top level method, so check for a bot decorator
        # needs a decorator with `command` in the last section and to be called
        visitor = _FindNeedsSelfDecorator()
        node.visit(visitor)
        if visitor.has_deco and not visitor.needs_self:
            self.found_errors.append(Actions.USING_SELF_ON_BOT_COMMAND)

            def update(node: libcst.FunctionDef):
                params = node.params.with_changes(params=node.params.params[1:])
                return node.with_changes(params=params)

            self.updates[node] = update


class CallbackRequiresSelfVisitor(BaseHelpTransformer):
    """Callbacks require self if they are not top level or have the proper decorators."""

    def visit_FunctionDef(self, node: libcst.FunctionDef):
        if not node.decorators:
            return False

        if node.params.params:
            first_param: libcst.Param = node.params.params[0]
            if first_param.name.value == "self":
                return False

        # its self and a top level method, so check for a bot decorator
        # needs a decorator with `command` in the last section and to be called
        visitor = _FindNeedsSelfDecorator()
        node.visit(visitor)
        if visitor.has_deco and visitor.needs_self:
            self.found_errors.append(Actions.MISSING_SELF_IN_EVENT_OR_COMMAND)

            def update(node: libcst.FunctionDef):
                params = list(node.params.params)
                params.insert(0, libcst.Param(libcst.Name("self")))
                return node.with_deep_changes(node.params, params=params)

            self.updates[node] = update


class ClientIsNotBot(BaseHelpTransformer):
    """Client should not be a Bot instance."""

    BOT_CLASSES = ("Bot", "InteractionBot")

    VAR_NAME = "client"

    def __init__(self):
        self.module = None
        super().__init__()

    def on_visit(self, node):
        if not self.module:
            self.module = node
        return super().on_visit(node)

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
            if target.target.value == self.VAR_NAME:
                found_client = True

                def possible_fix(module: libcst.Module):
                    # every single node of Name where the name is `client` needs to be changed to `bot`

                    class Fixer(libcst.CSTTransformer):
                        def __init__(self, var_name):
                            self.var_name = var_name

                        def leave_Name(
                            self, node: libcst.Name, updated: libcst.Name
                        ) -> libcst.Name:
                            if updated.value == self.var_name:
                                return updated.with_changes(value="bot")
                            return updated

                    return module.visit(Fixer(self.VAR_NAME))

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
        self.updates[self.module] = possible_fix


class _FindProcessCommands(libcst.CSTVisitor):
    """Finds all calls of a function named `process_commands()`"""

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
    """In an on_message event, the bot should call process_commands."""

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


class IncorrectTypeHints(BaseHelpTransformer):
    """Context objects typehinted with Interaction or vice versa."""

    def __init__(self):
        super().__init__()
        self._typehint = None

    def visit_FunctionDef(self, node: libcst.FunctionDef):
        # check if it is a command def
        if not node.decorators:
            return False
        visitor = _FindNeedsSelfDecorator()
        node.visit(visitor)
        if not visitor.has_deco:
            return False
        if visitor.deco in ("group", "command"):
            # check typehints for an interaction parameter
            self._typehint = ("Interaction", "Context")
            self._error = Actions.INCORRECT_CTX_TYPEHINT
        elif visitor.deco in ("slash_command", "message_command", "user_command"):
            # check typehints for a commands parameter
            self._typehint = ("Context", "Interaction")
            self._error = Actions.INCORRECT_INTERACTION_TYPEHINT
        return True

    def visit_FunctionDef_params(self, node: libcst.FunctionDef) -> None:
        if not node.params.params:
            # different error, no params
            return False
        params_list = list(node.params.params)
        # this runs after checking for self checking
        index = 0
        if params_list[0].name.value == "self":
            index = 1
        annotation = params_list[index].annotation
        if not annotation:
            return
        annotation = annotation.annotation
        typehint: libcst.Name = getattr(annotation, "attr", annotation).value
        if self._typehint[0] in typehint:
            self.found_errors.append(self._error)


class FindPassContext(BaseHelpTransformer):
    """Find anywhere someone uses pass_context. This should only check decorators, but you really don't need it anywhere."""

    def visit_Name(self, node):
        if node.value == "pass_context":
            self.found_errors.append(Actions.USED_PASS_CONTEXT)
