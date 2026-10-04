# Instagram Public Account Monitor

Hosted monitoring dashboard for the public Instagram account @amar.achi8774.

Records public profile metadata, bio, follower/following/post counts when exposed, profile-image changes, public post/Reel URLs, first-detected timestamps, change history and scan history. Repost baseline is 2; no repost timestamp is invented.

Only publicly accessible information is used. The monitor does not attempt private activity, private messages, hidden online status, private likes, or bypass platform restrictions. Instagram may limit what its public page exposes; unavailable fields remain unknown.

The instagram-monitor branch is separate from the Genie/main branch. Render can deploy the web dashboard and daily scan job from this branch.
