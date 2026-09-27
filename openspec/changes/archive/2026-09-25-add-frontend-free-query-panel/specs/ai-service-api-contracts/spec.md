## MODIFIED Requirements

### Requirement: Sale assistance groups results by family
The `POST /v1/assist/sale` request MUST accept a product identifier and a query as independent optional fields, and MUST require at least one of the two; a request carrying neither MUST be rejected as invalid. It MUST also accept the same optional catalog-side filters the retrieval request accepts, defaulting to no filter, so that a caller which omits the field receives the behaviour it received before the field existed. The response MUST expose `intent`, `groups`, `pitch`, `citations`, `warnings`, an optional `clarification_question`, `usage`, `abstained` and `prompt_version`. Each entry in `groups` MUST expose a `family_id` that MAY be null, and a group whose `family_id` is null MUST contain exactly one member. Every member of a group MUST expose `variant_label` and `match_reasons`. Every entry in `warnings` MUST belong to a closed vocabulary declared by the assistance capability. Every entry in `citations` MUST expose `citation_id`, `document_title`, `section_title`, `doc_type`, `claim_scope`, `score` and `snippet`, and MAY expose the `product_id` it supports.

#### Scenario: Assist response groups members under a family
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with a valid body in stub mode
- **THEN** the response includes `groups`
- **AND** each group exposes a `family_id`
- **AND** every group member exposes `variant_label` and `match_reasons`

#### Scenario: A group without a family carries a single member
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** every group whose `family_id` is null contains exactly one member

#### Scenario: The request requires at least one anchor
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with neither a product identifier nor a query
- **THEN** the response is a validation error
- **AND** the error names both fields as the alternatives

#### Scenario: The request accepts catalog-side filters
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with a query and catalog-side filters
- **THEN** the request is accepted
- **AND** the filters carry the same fields the retrieval request declares

#### Scenario: Omitting the filters is the previous behaviour
- **WHEN** an authenticated client calls `POST /v1/assist/sale` without the filters field
- **THEN** the request is accepted
- **AND** no filter is applied

#### Scenario: Citations carry their identifier and their claim scope
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** every returned citation exposes `citation_id`, `document_title`, `section_title`, `doc_type` and `claim_scope`

#### Scenario: The response declares abstention and prompt provenance
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** the response exposes `abstained`
- **AND** it exposes `prompt_version`, which MAY be null

## ADDED Requirements

### Requirement: The snapshot moves by pure addition, verified leaf by leaf

The regeneration of the committed OpenAPI snapshot for this change SHALL be verified to be a pure addition: no leaf of the previous snapshot MUST be removed and no leaf MUST change type, and the verification MUST be performed leaf by leaf against the previous snapshot rather than asserted.

The stub fixture of the assistance route MUST be kept consistent with the moved contract, and in particular MUST NOT emit the price or stock placeholders in the free-query mode, because a fixture exempt from a rule the real path enforces is the one response a client learns the wrong shape from.

#### Scenario: The snapshot movement is a pure addition
- **WHEN** the regenerated snapshot is compared with the previous one
- **THEN** no leaf was removed
- **AND** no leaf changed type
- **AND** the comparison is reported leaf by leaf

#### Scenario: The stub does not emit placeholders in the free-query mode
- **WHEN** the stub serves a request carrying a query and no product identifier
- **THEN** the returned argument contains neither the price placeholder nor the stock placeholder
