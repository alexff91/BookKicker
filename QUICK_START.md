# BookKicker 2.0 - Quick Start Guide

## 🚀 Quick Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migration

```bash
# Dry run first (recommended)
python migrate_database.py --dry-run

# Actual migration
python migrate_database.py
```

### 3. Start Bot

```bash
# Test mode
python telebot_handler_improved.py

# Production mode
python telebot_handler_improved.py --prod
```

---

## 📱 User Guide

### Main Menu

After sending `/start` or `/menu`, you'll see:

```
┌─────────────────────────┐
│   📖 BookKicker Menu    │
├─────────────────────────┤
│ [📖 Read more]          │
│ [📚 My library]         │
│ [⚙️ Settings]           │
│ [📊 Statistics]         │
│ [❓ Help]               │
└─────────────────────────┘
```

### Reading a Book

1. **Upload** - Send .epub, .fb2, or .txt file to bot
2. **Read** - Click "📖 Read more" or send `/more`
3. **Navigate** - Use inline buttons:
   - 📖 More - Get next portion
   - ⏩ Skip - Skip ahead ~100 lines
   - 🔖 Bookmark - Save current position

### Library Management

1. Click "📚 My library" in main menu
2. See all your books with progress bars
3. Select a book to:
   - Read from it
   - Set as current book
   - View bookmarks
   - See details

### Settings

Click "⚙️ Settings" to configure:

- **🔄 Auto-send** - Automatic text delivery
- **🌍 Language** - Interface language (Русский/English)
- **⏰ Frequency** - How often to send (1-12 times/day)
- **🔊 Audio mode** - Text-to-speech
- **📏 Chunk size** - Text portion size
- **🌐 Timezone** - Your time zone

### Statistics

Click "📊 Statistics" to view:

- **Total books** read
- **Lines and characters** read
- **Reading sessions** count
- **Weekly/monthly** breakdowns
- **First and last** reading dates

### Bookmarks

While reading:
1. Click 🔖 to save position
2. Go to Library → Select book → 🔖 Bookmarks
3. Click bookmark to jump to that position

---

## 🎯 Quick Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot and show main menu |
| `/menu` | Show main menu |
| `/more` | Read next portion |
| `/skip` | Skip ahead in book |
| `/help` | Show help message |
| `/stats` | Show reading statistics |
| `/library` | Show your library |

---

## 📊 Progress Tracking

Books now show progress:

```
📖 War and Peace
✍️ Leo Tolstoy
📊 Progress: 1,234/5,678 lines (21.7%)
▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱ 21.7%
```

---

## ⚙️ Settings Explained

### Auto-send

When enabled, bot automatically sends text portions based on your frequency setting.

**Frequencies:**
- 1x/day - Once at noon
- 2x/day - Morning and evening
- 4x/day - Every 4 hours
- 6x/day - Every 2-3 hours
- 12x/day - Every hour (7 AM - 9 PM)

### Chunk Size

Controls how much text you get per portion:

- **Small (500)** - Quick reads
- **Medium (893)** - Default, balanced
- **Large (1500)** - Longer sessions
- **Very Large (2500)** - Maximum length

### Audio Mode

When enabled:
- Text is sent as voice message
- Language auto-detected (Russian/English)
- Works with any book

---

## 🔖 Bookmarks Usage

### Add Bookmark

**While Reading:**
1. See text you want to bookmark
2. Click 🔖 Bookmark button
3. Bookmark saved at current position

### View Bookmarks

**From Library:**
1. Main Menu → 📚 Library
2. Select book
3. Click 🔖 Bookmarks
4. See all saved positions

### Jump to Bookmark

1. Click on a bookmark
2. Bot sends text from that position
3. Continue reading from there

---

## 📈 Statistics Explained

### Total Stats

- **Total books**: Unique books you've read
- **Lines read**: Total lines across all books
- **Characters read**: Total characters read
- **Sessions**: Number of times you've read

### Weekly/Monthly

View daily breakdown:
```
📅 2024-11-16: 234 lines
📅 2024-11-15: 456 lines
📅 2024-11-14: 189 lines
```

Track your consistency and reading habits!

---

## 🎨 New Features Highlights

### ✅ What's New

- **Interactive Menus** - No more typing commands
- **Progress Bars** - Visual reading progress
- **Bookmarks** - Save positions
- **Statistics** - Track reading habits
- **Better Settings** - Customize everything
- **Multi-language Audio** - Auto-detects language
- **Performance** - Much faster responses

### 🔒 Security

- All data protected from SQL injection
- Secure database connections
- Proper error handling

### ⚡ Performance

- 5-10x faster database operations
- Connection pooling
- Optional Redis caching
- Optimized queries

---

## 🐛 Common Issues

### "No book found"

**Solution:** Upload a book first or check Library

### "Error loading book"

**Solutions:**
- Ensure file is .epub, .fb2, or .txt
- Check file isn't corrupted
- Try re-uploading

### Auto-send not working

**Check:**
- Auto-send enabled? (⚙️ Settings → 🔄 Auto-send)
- Current book set? (📚 Library → Select book)
- Frequency configured? (⚙️ Settings → ⏰ Frequency)

### Progress shows 0%

**Reason:** Old books need re-upload for progress tracking

**Solution:** Upload book again or wait for automatic calculation

---

## 💡 Pro Tips

### Tip 1: Customize Reading Experience

Set chunk size based on your reading speed:
- Commute? Use Small (500)
- Lunch break? Use Medium (893)
- Evening? Use Large (1500)

### Tip 2: Use Auto-send Wisely

- Morning person? Set 6x/day starting at 7 AM
- Prefer evenings? Set 2x/day (afternoon + evening)
- Weekend reader? Turn off auto-send during week

### Tip 3: Bookmark Important Parts

- Favorite quotes
- Where you want to discuss
- Confusing parts to revisit
- Chapter starts

### Tip 4: Track Your Progress

Check stats weekly to:
- See reading consistency
- Set goals
- Celebrate milestones
- Stay motivated

### Tip 5: Audio Mode for Multitasking

Enable audio when:
- Commuting
- Exercising
- Cooking
- Walking

---

## 📚 Supported File Formats

- **.epub** - Most e-books
- **.fb2** - FictionBook format
- **.txt** - Plain text

**Coming soon:** PDF support

---

## 🌍 Languages

### Interface Languages

- 🇷🇺 Russian
- 🇬🇧 English

### Audio Languages

Auto-detected from text:
- Russian
- English

---

## 📞 Support

### Need Help?

1. Send `/help` in bot
2. Check [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)
3. Report issues on GitHub

### Feature Requests

Have ideas? We'd love to hear them! Create an issue on GitHub.

---

## 🎉 Enjoy Reading!

BookKicker 2.0 makes reading easier and more enjoyable. Start reading incrementally, track your progress, and build consistent reading habits!

**Happy Reading! 📖**
