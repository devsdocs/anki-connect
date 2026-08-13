# AnkiConnect Custom Patches

This fork of AnkiConnect contains a custom patch for the `answerCards` endpoint.

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
