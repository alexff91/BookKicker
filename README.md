# Book Kicker
Telegram bot. https://telegram.me/BookKicker_bot

Allows reading book via telegram. 

Reminds every day with a little piece of text

Input file format: .epub

Output: message with the next piece of text

Auto-send every hour.


##Start server
nohup python3 telebot_handler.py /dev/null 2>&1&

###How to run

Create a file tokens.py (will be moved to .env or config later)
```
test_token='bot_token'
production_token='bot_token'
ruvds_server_ip='bot_server_ip'
user="db_user"
password="db_pass"
host="db_server"
db="db_name"
```

You will need database(Postgres) and host with public ip (for incoming webhooks from tg).
Then run ```pip install -r /path/to/requirements.txt```

To run server - run ```nohup python3 telebot_handler.py /dev/null 2>&1&```



