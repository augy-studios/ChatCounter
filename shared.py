# In-memory user message stats
stats = {}
max_id = 0

# In-memory word usage stats: key=(guild_id, word)
# value: { 'id', 'word_id', 'guild_id', 'word', 'count', 'is_dict' }
words_stats = {}
max_word_id = 0