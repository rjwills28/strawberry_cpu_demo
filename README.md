# strawberry_cpu_demo
The provides a small demo Strawberry GraphQLserver and corresponding Python client that can be used to demonstrate the difference in 
CPU usage when using the 2 different websocket protocols: graphql-ws (legacy) and graphql-transport-ws.

The client will create *n* number of subscriptions to the Strawberry GraphQL server and wait to collect *x* number of samples. 
During this time it monitors the CPU usage of the Strawberry server application. Once *x* samples have been collected it computes
the average CPU usage over the time that the subscriptions were made and print the final value. 

 
 ## Prerequisites 
 - Python > 3.7
 
 ## Installation
 - Clone this repo.
 - Create a Python virtual environment to install dependencies and run code.
 
    `python -m venv venv`
    
    `source venv/bin/activate`
- Install dependencies from setup file:

  `python setup.py install`
  
## Running the tests
To demonstrate the difference in CPU usage please follow this test setup

- In one terminal, start the server:

  `demo_strawberry_server`

- In a second terminal (with the venv activate) run the client tests:

  `demo_strawberry_client -n 100 -s 200 -p 1`
  
  `demo_strawberry_client -n 100 -s 200 -p 2`

  where:
  
    - n <number> = number of subscriptions
    - s <number> = number of samples to collect
    - p <1 or 2> = the websocket protocol to use: 
        - 1 = graphql-ws
        - 2 = graphql-transport-ws
