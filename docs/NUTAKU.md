## Storage location

The save is not persisted client-side. The real save lives server-side on Sad Panda's own BlayFap backend, reached by
first exchanging a Nutaku-issued identity token for a BlayFap session (`LoginWithNutaku`), then fetching the save fresh
each launch (`GetDynamoUserSession`).

Two distinct JWTs are involved, both using the same unusual `alg` - the verbose URI form
`http://www.w3.org/2001/04/xmldsig-more#hmac-sha256` rather than the usual `HS256`, a useful fingerprint for spotting
either in a Network tab capture:

- **Nutaku's own token** (sent as `CustomId` in the `LoginWithNutaku` request) - payload `{"ID": "<NutakuId>", "exp":
  ..., "flags": 0}`, `NutakuId` being the player's Nutaku platform account ID. Presumably supplied to the Unity build by
  Nutaku's own wrapper page/SDK - out of this project's scope to source further.
- **BlayFap's session token** (returned as `AuthToken` from `LoginWithNutaku`, sent back as the `X-Authorization`
  header on every later BlayFap call) - payload `{"ID": "<BlayFapId>", "exp": ..., "flags": 0}`, `ID` mirroring
  `BlayFapId`. Observed expiry is about a week out from issue.

## Endpoints

Host: `blayfap-ca.sadpandastudios.com`

### Login: `POST /login/LoginWithNutaku`

```
curl 'https://blayfap-ca.sadpandastudios.com/login/LoginWithNutaku' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://gi.nutaku.com' \
  -H 'Referer: https://gi.nutaku.com/' \
  --data-raw '{"CreateAccount":false,"ReactivateAccount":false,"VersionIdentifier":"<build id>","DeviceInfo":{"DeviceModel":"<browser+version>","DeviceType":"Desktop","OperatingSystem":"...","OperatingSystemFamily":"...","Memory":<bytes>,"Resolution":"(<w>,<h>)","Language":"en-US","GameLanguage":"en-US","PushAllowed":false},"CustomId":"<Nutaku JWT>"}'
```

- `VersionIdentifier` closely tracks `GameState.Build`'s suffix - e.g. request `007b49` alongside a same-session save's
  `Build: "449_007b499"`. Not confirmed as an exact substring rule (one character short here) - likely a build hash
  truncated/abbreviated differently on each side rather than a literal match.
- `DeviceInfo` is a browser/device fingerprint block; fields are self-explanatory and don't affect the save.
- `CustomId` is the Nutaku JWT described above, not a BlayFap-issued token.
- No `X-Authorization` header yet - this call is what obtains one.

Response body:

```json
{
  "EventData": null,
  "CatalogId": null,
  "AdsConfig": null,
  "ManifestHash": null,
  "BlayFapId": <BlayFapId>,
  "Created": false,
  "PendingDeletion": false,
  "AuthToken": "<BlayFap JWT>",
  "AuthExpiration": "<ISO 8601, matches AuthToken's exp>",
  "CreationDate": "<ISO 8601>",
  "Error": null
}
```

- `BlayFapId` and `AuthToken` are exactly what `GetDynamoUserSession`/`UpdateDynamoUserSession` need afterward.
- `EventData`/`CatalogId`/`AdsConfig`/`ManifestHash` were all `null` in the one capture - shape/purpose when non-null is
  unconfirmed.
- `Created`/`PendingDeletion`/`CreationDate` read as account lifecycle bookkeeping; not explored further.

### Fetch: `POST /client/GetDynamoUserSession`

```
curl 'https://blayfap-ca.sadpandastudios.com/client/GetDynamoUserSession' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Authorization: <BlayFap AuthToken>' \
  -H 'Origin: https://gi.nutaku.com' \
  -H 'Referer: https://gi.nutaku.com/' \
  --data-raw '{"BlayFapId":<BlayFapId>}'
```

Response body:

```json
{
  "Session": "<lzfc... blob>",
  "SessionID": <int>,
  "Error": null
}
```

`Session` is the save blob, in the same text container as [Switch](structure/RAW.md#nintendo-switch):
`base64(MAGIC)` + `base64(lzf_compress(plaintext))` concatenated as text, rendering as the `lzfc...` prefix. Unlike the
Switch file, there's no leading 4-byte binary header to skip, so it decodes with the existing PC-mode path unchanged -
`tools/crushcrush_save.py decode` on the blob as-is, no code changes needed.

### Save: `POST /client/UpdateDynamoUserSession`

```
curl 'https://blayfap-ca.sadpandastudios.com/client/UpdateDynamoUserSession' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Authorization: <BlayFap AuthToken>' \
  -H 'Origin: https://gi.nutaku.com' \
  -H 'Referer: https://gi.nutaku.com/' \
  --data-raw '{"BlayFapId":<BlayFapId>,"Session":"<lzfc... blob, same format as the fetch response>","SequenceID":<int>,"SessionID":<int>}'
```

- `Session` is the encoded save blob, same format as `GetDynamoUserSession`'s response.
- `SessionID` is echoed straight from the preceding `GetDynamoUserSession` response's `SessionID` - confirmed by a
  matching paired fetch/update capture.
- `SequenceID` is an extra field with no fetch-side counterpart seen yet; was `0` in the one sample captured.
- A response of `{"Error": null}` with HTTP 200 means the POST succeeded. This makes push/pull against this API (rather
  than only local `.sav` files) a viable path for a future editor UI, not just a read-only investigation.
- Implementation gotcha: curl's `--data-raw @file` does **not** read from the file - only `--data`/`--data-binary` do.
  `--data-raw` sends the literal string, so `--data-raw @body.json` silently POSTs the text `@body.json` and gets a
  content-free `400`. Use `--data-binary @file` when the body is large enough to need a file instead of an inline
  string.

## Open questions

- What `SequenceID` tracks, and whether the server validates or increments it - `0` was accepted in the one write
  tested, but that doesn't confirm it's ignored.
- Whether `flags` ever varies on either JWT, and what it gates.
- Whether `BlayFapId` stays stable across repeated `LoginWithNutaku` calls for the same Nutaku account (plausible, since
  it's presumably derived deterministically from the Nutaku identity) - not tested across multiple logins.
- Shape/purpose of `EventData`/`CatalogId`/`AdsConfig`/`ManifestHash` when non-null.
- Where/how the client obtains the Nutaku `CustomId` JWT in the first place - presumably from Nutaku's own wrapper
  page/SDK, not traced further here.
- Any relationship between this BlayFap session and PlayFab's separate account-authoritative data (`Playfab.Inventory`/
  `Participation`, `BlayfapAwardedItems` - see [UNLOCKS.md](UNLOCKS.md)). The `BlayFapId`/
  `BlayfapAwardedItems` naming overlap is suggestive but unconfirmed.
