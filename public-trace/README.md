# PublicTrace

A separate public-web investigation dashboard.

## Included
- Public phone-number web discovery for a supplied number.
- Search links scoped to major social platforms and news/images.
- Client-side Google Lens image upload for finding copies, similar images, and pages containing the same/similar image.
- No private WhatsApp presence tracking, messages, hidden likes, or account access.
- No assertion that a visual match proves a person's identity.

Google documents that Lens can return similar images and websites containing the image or a similar image. The dashboard uses Google's public Lens upload flow from the browser.

## Run
gunicorn --chdir public-trace app:app --bind 0.0.0.0:$PORT
