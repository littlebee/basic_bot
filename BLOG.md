# Lazy Blog

This is a lazily updated, lazily set up -- who needs Medium <explenity> blog updated by a lazy engineer more interested in doing than writing about it.


## Sept 12 2025  -- Summer is canceled!

Technically speaking, summer ended on it's own terms, but ✅ all the happy homeowner chores are complete, ✅ went on multiple camping trips with Daphne and Vanhilda, and ✅ homesite secured for 🥶.

Winter is comming and we are back in a big way.

💥 Added WebRTC video streaming, it works well, and also adds audio streaming.
💥 Recorded videos now include audio track in the .mp4 files recorded.

See [daphbot-due](https://github.com/littlebee/daphbot-due/pull/50) for examples of both new features.


## Mar 15, 2025  -- Recorded video and retrieval via REST interfaces available

You can see an example of it's use in the daphbot-due example's [webapp](https://github.com/littlebee/daphbot-due/tree/main/webapp/src/VideoViewer) and it's [behavior service](https://github.com/littlebee/daphbot-due/blob/663d2b59da79959d74c48bcc61e28dfc69c4b72d/src/daphbot_service.py#L75).

## Feb 8, 2025  -- Added support for PI Camera 2 🎉

https://github.com/littlebee/basic_bot/pull/51

Allows using a pi ribbon cable cameras on Raspberry Pi 4 or 5.

## Jan 28, 2025  -- We have [online hosted docs](https://littlebee.github.io/basic_bot/)! 🎉

## Jan 27, 2025  -- It can see!

Working basic_bot.services.vision_cv service that uses open cv2 and tensorflow lite.  Still trying to decide what else is needed in the beta version - support for GPIO in?  Doing this in parallel with implementing the first working example of using basic_bot - [daphbot-due](https://github.com/littlebee/daphbot-due)


## Jan. 20, 2025  -- Basic working central_hub and web_server services merged.

Working on adding basic motor controller service similar to Scatbot.
