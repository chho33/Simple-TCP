## File Descriptions

### tcp_client.py

The code for running the client.

### tcp_server.py

The code for running the server.

### args_client.py

Arguments for the client.

### args_server.py

Arguments for the server.

### utils.py

Utilities that common for server and client. Includes: create packet, parse packet, checksum, and other useful functions.

### settings.py

Defines some constant values.



## Commands Explanation

### Server

Follows the format of the project description - `tcpserver file listening_port address_for_acks port_for_acks`.

There are $4$ positional arguments must be assigned manually and it's mandatory:

- `file`: The file path for writing the data.
- `listening_port`: The port server is running on.
- `address_for_acks`: The address for sending the ACKs.
- `port_for_acks`: The port for sending the ACKs.

There are also $3$ optional arguments (need to use `--` to assign them.)

- `max_seq_no`: Maximum sequence number. Default is $2^{32} -1$.
- `max_data_size`: Maximum data size for a segment. Default is $20$ (bytes).
- `window_size`: Window size. Default is $100$.

**Example:**

Run the server on port `41194`, and send the ACKs to `localhost:41191`. The maximum data size is $99$, maxmimum sequence number is $150$, and the window size is $100$.


```python
python tcp_server.py output.txt 41194 localhost 41191 --max_data_size 99 --max_seq_no 150 --window_size 100
```

### Client

Follows the format of the project description - `tcpclient file address_of_udpl port_number_of_udpl windowsize ack_port_number`.

There are $5$ positional arguments must be assigned manually and it's mandatory:

- `file`: The file path for reading the data.
- `address_of_udpl`: The address of the newudpl service for sending packets to.
- `port_number_of_udpl`: The port of the newudpl service for sending packets to.
- `windowsize`: Window size.
- `ack_port_number`: The client port for receiving the ACKs.

There are also $2$ optional arguments (need to use `--` to assign them.)

- `max_seq_no`: Maximum sequence number. Default is $2^{32} -1$.
- `max_data_size`: Maximum data size for a segment. Default is $20$ (bytes).

**Example:**

Run the client on port `41191` , and send packets to `localhost:41192`. The maximum data size is $99$, maxmimum sequence number is $150$, and the window size is $100$.

```python
python tcp_client.py hello.txt localhost 41192 100 41191 --max_data_size 99 --max_seq_no 150
```

**\* Important: The `windowsize` argument of the client should be equal to the `window_size` argument of the server, and the `max_seq_no` and the `max_data_size` of both server and client should be equal.**

### Features

- Any window size that is bigger than the data size is available.
- This project take shortage of the sequence number into account that avoid the error when the sequence number exceeds the limit. It will be wrapped around.
- The program can deal with any maximum data size of a segment.
- Dynamic timeout. If timeout happens frequently at the client, it will increase the timeout time. Otherwise, it will shrink the timeout time to $1$ second.

### More Detail

https://docs.google.com/document/d/1oG2rBz54yhtGVNEhUAMgZOvo9UWjqFu3P2p47E1sanA/edit