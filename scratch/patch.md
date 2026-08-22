# AnkiConnect Custom Patches

This fork of AnkiConnect contains custom patches for the `answerCards` and `sync` endpoints.

#### `sync`
*   Synchronizes the local Anki collection with AnkiWeb, gracefully handling single-client concurrency rules and edge cases.
    *   **AnkiWeb Single-Client Concurrency**: Gracefully detects and reports when AnkiWeb is busy or another client is currently synchronizing the account.
    *   **Eliminates Redundant Double Sync**: Removes duplicate collection sync previously triggered via `mw.onSync()`, eliminating race conditions and blocking GUI dialog popups.
    *   **Local Concurrency Lock**: Protects against concurrent API sync requests with an internal non-blocking lock.
    *   **Active Media Sync Guard**: Checks if background media sync is in progress before initiating collection sync.
    *   **Auth Token Management**: Clears stale credentials on authentication failures (`SyncErrorKind.AUTH`).
    *   **Full Sync Direction Handling**: Catches and clearly communicates when full one-way sync (`FULL_SYNC`, `FULL_DOWNLOAD`, `FULL_UPLOAD`) is required.
    *   **Post-Sync Maintenance**: Automatically updates host number, server endpoints, reloads scheduler, flushes model cache, runs GUI hooks, refreshes the UI, and dispatches background media sync when enabled.

    <details>
    <summary><i>Sample request:</i></summary>

    ```json
    {
        "action": "sync",
        "version": 6
    }
    ```
    </details>

    <details>
    <summary><i>Sample result:</i></summary>

    ```json
    {
        "result": null,
        "error": null
    }
    ```
    </details>

#### `answerCards`
*   Answer cards. Ease is between 1 (Again) and 4 (Easy). Optionally, you can pass a `time` in milliseconds to specify the time taken to answer the card (this overrides the default timer behavior). Returns `true` if card exists, `false` otherwise.

    <details>
    <summary><i>Sample request:</i></summary>

    ```json
    {
        "action": "answerCards",
        "version": 6,
        "params": {
            "answers": [
                {
                    "cardId": 1498938915662,
                    "ease": 2,
                    "time": 15000
                }
            ]
        }
    }
    ```
    </details>
