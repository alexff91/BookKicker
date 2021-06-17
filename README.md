# Book Kicker
Telegram bot. https://telegram.me/BookKicker_bot

Allows reading book via telegram. 

Reminds every day with a little piece of text

Input file format: .epub

Output: message with the next piece of text

Auto-send every hour.

Commands:

/start - initialisation

/more - force request next peace of text

/help - other info

##Start server
nohup python3 telebot_handler.py /dev/null 2>&1&


P.S. Based on https://github.com/axtrace/PartyBook