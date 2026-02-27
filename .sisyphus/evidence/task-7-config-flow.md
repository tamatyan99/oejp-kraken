# Evidence: Task 7 - Config Flow and Japanese translations

- Implemented UI Config Flow for OEJP Kraken integration
- Created config_flow.py under custom_components/oejp_kraken/
- Updated translations/ja.json with improved Japanese description for update interval
- Implemented user input form with fields:
  - email (required)
  - password (required)
  - update_interval (optional, default 300 seconds)
- Added input validation for email format, non-empty password, and update_interval range defaulting
- Integrated GraphQL authentication test using KrakenGraphQLClient.authenticate()
- Errors surfaced to UI as cannot_connect, invalid_auth, or unknown
- Evidence file includes plan and commit notes reference
