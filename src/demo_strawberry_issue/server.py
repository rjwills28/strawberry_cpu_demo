import asyncio
from typing import AsyncIterator, List, Optional

from aiohttp import web
from strawberry.aiohttp.views import GraphQLView
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class SubSubSubSubClass():
    name: str
    running: bool


@strawberry.type
class SubSubSubClass():
    name: str
    running: bool
    nested: SubSubSubSubClass


@strawberry.type
class SubSubClass():
    name: str
    running: bool
    nested: List[SubSubSubClass]


@strawberry.type
class SubClass():
    name: str
    nested: SubSubClass
    empty: Optional[bool]


@strawberry.type
class Demo:
    name: str
    val: int
    arr : List[int]
    nested: SubClass


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def getValue(self, id: strawberry.ID) -> Demo:
        count = 0
        while True:
            sub_list = [
                SubSubSubClass(name="name1",running=True, nested=SubSubSubSubClass(name="name1",running=True)),
                SubSubSubClass(name="name2",running=True, nested=SubSubSubSubClass(name="name2",running=True)),
                SubSubSubClass(name="name3",running=True, nested=SubSubSubSubClass(name="name3",running=True)),
                SubSubSubClass(name="name4",running=True, nested=SubSubSubSubClass(name="name4",running=True))
            ]
            res = Demo(
                    name="test", 
                    val=count, 
                    arr = [count,count+1,count+2,count+3],
                    nested = SubClass(
                        name="test1", 
                        nested = SubSubClass(name="test2", running=True, nested = sub_list),
                        empty= None))
            yield res
            count += 1
            await asyncio.sleep(0.1)


class MyGraphQLView(GraphQLView):
    async def get_context(self, request: web.Request, response: web.StreamResponse):
        return {"request": request, "response": response}


def main(args=None) -> None:
    schema = strawberry.Schema(query=Query, subscription=Subscription)

    view = MyGraphQLView(
        schema=schema,
        subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL],
    )

    app = web.Application()
    app.router.add_route("*", "/ws", view)
    web.run_app(app)


if __name__ == "__main__":
    main()