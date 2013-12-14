# RabbiTornado

## Introduction

**RabbiTornado** is a Python Tornado Framework based Web Server that implements multi-user chat (think IRC) via WebSockets. The message delivery backend is RabbitMQ... Hence the name RabbiTornado.

## Installation

### Prerequisites

* Python 2.7
* RabbitMQ (<http://www.rabbitmq.com>)
* Tornado Framework (use `sudo easy_install tornado`)
* Pika RabbitMQ module (use `sudo easy_install pika`)

### Installation
* Nothing much to be done

### Running
1. Ensure that RabbitMQ is running
2. Run the Server by typing `python main.py`
3. This will run the server on port 8888  (edit main.py if you want to change the port)
4. Open up a browser to <http://localhost:8888/>

### Configurations
* The Server listening port an be configured in `main.py`
* The RabbitMQ server connection information can be configured via the `amqp_url` variable in `main.py`
* The login database is currently hardcoded in `authenticator.py`, the only login at this moment is user `charles` with password `foobar`

### Notes
* Currently `authenticator.py` allows for 3 methods of login authentication. A MySQLdb query, hard coded in-memory dictionary and full_public mode which just lets anyone in with whatever user/password combination. full_public is the current default. Change it as you see fit.

### TODO
* Implement the room chat backlog `logger.py` to be able to get a history/backlog of messages
* Integrate with a regular IRC server
* An configuration system rather than hardcoding everything