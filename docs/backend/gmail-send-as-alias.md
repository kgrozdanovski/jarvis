With Google Workspace, you usually **do not need to pay for another user** just to have `no-reply@yourdomain.com`.

The best option is to create `no-reply@yourdomain.com` as an **alias** on your existing paid mailbox.

Google Workspace lets you add up to **30 email aliases per user at no extra cost**. ([Google Workspace Help][1])

## Option 1: Use an email alias — simplest

In Google Admin:

1. Go to **Admin console**
2. Go to **Directory → Users**
3. Click your existing user, e.g. `you@yourdomain.com`
4. Open **Alternate email addresses / Email aliases**
5. Add:

```txt
no-reply@yourdomain.com
```

Now emails sent to `no-reply@yourdomain.com` will land in your existing inbox.

Then in Gmail, configure sending from it:

1. Open Gmail
2. Go to **Settings → See all settings**
3. Go to **Accounts and Import**
4. Under **Send mail as**, add `no-reply@yourdomain.com`
5. Verify it
6. Optionally make it the default for certain use cases

Google’s Gmail settings support sending from another address or alias and setting a different reply-to address. ([Google Help][2])

## Important caveat

A true “no-reply” address is not ideal for normal customer communication. It can frustrate users and sometimes hurts deliverability/engagement.

A better setup is often:

```txt
notifications@yourdomain.com
```

or

```txt
hello@yourdomain.com
```

Then set a `Reply-To` header to your real inbox, such as:

```txt
support@yourdomain.com
```

For transactional emails, though, `no-reply@...` is common.

## Option 2: Use a Google Group

You can also create a Google Group like:

```txt
no-reply@yourdomain.com
```

and route messages to yourself or nobody.

This is useful if multiple people should receive messages later, but for your case an **alias is cleaner**.

## My recommendation

Create these aliases on your existing paid user:

```txt
hello@yourdomain.com
support@yourdomain.com
notifications@yourdomain.com
no-reply@yourdomain.com
```

Use `notifications@...` or `no-reply@...` for automated emails, and `hello@...` or `support@...` for real conversations. This keeps everything under one paid Google Workspace user.

[1]: https://knowledge.workspace.google.com/admin/users/add-or-delete-an-alternate-email-address-email-alias?utm_source=chatgpt.com "Add or delete an alternate email address (email alias)"
[2]: https://support.google.com/mail/answer/22370?hl=en&utm_source=chatgpt.com "Send emails from a different address or alias - Gmail Help"
