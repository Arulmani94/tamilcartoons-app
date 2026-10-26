-- Replaces ONLY the observed sample link for Episode 1.
-- Run in Supabase SQL Editor. If no rows return, inspect the episode in Admin.
UPDATE public.episodes
SET telegram_channel_id = '-1004309976850',
    telegram_message_id = 19,
    telegram_link = 'https://t.me/c/4309976850/19'
WHERE id = 1
  AND telegram_channel_id = '-1001234567890'
  AND telegram_message_id = 1
  AND telegram_link = 'https://t.me/c/1234567890/1'
RETURNING id, episode_number, telegram_link;
