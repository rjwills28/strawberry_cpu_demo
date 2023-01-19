import asyncio
import psutil
import time
import json
import websockets
import threading
import argparse


# Constants
cpu_average = 0
PV_PREFIX = "TEST:SUB"
thread_list = []

parser = argparse.ArgumentParser(description='Process inputs')
parser.add_argument(
    "-n", 
    "--nsubs", 
    action="store",
    dest="n_subs", 
    default=1,
    help="Number of subscriptions"
    )
parser.add_argument(
    "-s", 
    "--nsamples", 
    action="store",
    dest="n_samples", 
    default=10,
    help="Number of samples to collect"
    )
parser.add_argument(
    "-p", 
    "--protocol", 
    action="store",
    dest="ws_protocol", 
    choices=['1', '2'],
    default=1,
    help="websocket protocol: 1 = graphql-ws, 2 = graphql-transport-ws"
    )


class GraphQLClient:
    def __init__(self, endpoint, signal, ws_protocol):
        self.endpoint = endpoint
        self.signal = signal
        self.ws_protocol = ws_protocol

    async def subscribe(self, query, handle, n_messages):
        connection_init_message = json.dumps(
            {"type": "connection_init", "payload": {}}
        )

        request_message_graphql_ws_protocol = json.dumps(
            {"type": "start", "id": "id", "payload": {"query": query}}
        )

        request_message_graphql_transport_ws_protocol = json.dumps(
            {"type": "subscribe", "id": "id", "payload": {"query": query}}
        )

        protocols = ["graphql-ws", "graphql-transport-ws"]

        async with websockets.connect(
            self.endpoint,
            subprotocols=[protocols[self.ws_protocol-1]],
        ) as websocket:
            await websocket.send(connection_init_message)
            if self.ws_protocol == 2:
                await websocket.send(request_message_graphql_transport_ws_protocol)
            else:
                await websocket.send(request_message_graphql_ws_protocol)

            msg_count = 0
            async for response in websocket:
                data = json.loads(response)
                if data["type"] == "connection_ack":
                    pass
                elif data["type"] == "ka":
                    pass
                else:
                    if self.signal.get_start():
                        handle(data["payload"])
                        if n_messages == None:
                            # Do nothing and continue subscription indefinitely
                            pass
                        else:
                            if msg_count > n_messages:
                                break
                                print("break")
                            msg_count = msg_count + 1
                    else:
                        continue


class StartStopSignal():
    def __init__(self):
        self.start = False
        self.stop = False

    def signal_start(self):
        print("-> Starting monitor")
        self.start = True

    def signal_stop(self):
        print("-> Stopping monitor")
        self.stop = True

    def get_start(self):
        return self.start

    def get_stop(self):
        return self.stop


def cpu_monitor(signal):
    pid = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info["name"] == "demo_strawberry":
            pid = proc.info["pid"] 
            print("-> Monitoring PID: "+str(pid))
            break

    p = psutil.Process(pid)
    cpu_res = []
    while True:
        if signal.get_stop():
            break
        if signal.get_start():
            cpu = p.cpu_percent(interval=1.0)
            print("-> CPU: "+str(cpu))
            cpu_res.append(cpu)
        time.sleep(0.1)
    # Remove last element which may have been taken after subscriptions finished
    cpu_res.pop()
    if len(cpu_res) > 0:
        cpu_aver = sum(cpu_res)/(len(cpu_res))
        global cpu_average 
        cpu_average = cpu_aver


def get_subscription_query(name):
    return ("""subscription {
  getValue(id: "%s"){
    name
    val
    arr
    nested{
      name
      nested {
        name
        running
        nested {
          name,
          running
          nested {
            name
            running
          }
        }
      }
      empty
    }
  }
}
 """ % name)


def data_handler(data):
    # Do something with the data
    pass


def subscription(client, id, n_samples):
    asyncio.run( client.subscribe(query=get_subscription_query(id), n_messages=n_samples, handle=data_handler))


def main():
    args = parser.parse_args()
    n_subs = int(args.n_subs)
    n_samples = int(args.n_samples)
    ws_protocol = int(args.ws_protocol)

    protocol = "graphql-ws"
    if ws_protocol == 2:
        protocol = "graphql-transport-ws"
    print("-> Using the websocket protocol: '"+protocol+"'")

    # Create and start subscriptions
    signal = StartStopSignal()
    client = GraphQLClient(endpoint="ws://0.0.0.0:8080/ws", signal=signal, ws_protocol=ws_protocol)
    t = threading.Thread(target=cpu_monitor, args = (signal,))
    t.start()
    print("-> Starting subscriptions")
    for i in range(n_subs):
        id = PV_PREFIX + str(i)
        t = threading.Thread(target=subscription, args = (client, id, n_samples,))
        thread_list.append(t)
        t.start()

    # Monitor subscription progress
    signal.signal_start()
    list_size_t0 = len(thread_list)
    while True:
        for thread in thread_list:
            if not thread.is_alive():
                thread_list.remove(thread)
                if len(thread_list) == list_size_t0 - 1:
                    print("-> Subscriptions starting to close")
                    signal.signal_stop()
        if len(thread_list) == 0:
            break
        time.sleep(0.1)

    # Collect results
    time.sleep(1)
    print("\n ****** SUMMARY ******")
    print(" CPU average: "+str(cpu_average)+" %")
    print(" *********************\n")


if __name__ == "__main__":
    main()