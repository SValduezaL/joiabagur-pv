# pf-delivery-package Specification

## Purpose
What the AI final project's delivery package has to let a reviewer check, and by what criterion — the contract of the artefacts an evaluator who did not build this system reads: the delivery README whose structure is fixed by the submission template and whose template-owned sections are therefore frozen, reported with proposed text rather than edited; the evidence report that carries every figure the package publishes; and the demonstration script that walks the deployed environment. Its governing rule is that a claim which cannot be reproduced is not published as a figure. Counts of archived changes state the unit they counted, and the canonical unit is a directory of `openspec/changes/archive/`, because that is the only figure a reader reproduces in a single command without reading the project plan — the document whose own counts were in doubt; a count in fichas of the plan is labelled as such and stated beside the directory count rather than in place of it, a criterion that classifies by date names every exception it applies rather than leaving a reader to apply the rule and arrive at a different number, and duplicate directories are declared rather than removed, since rearranging the historical archive so a total adds up is the opposite of making a figure verifiable. The taxonomy of search methods carries one row per method with a figure taken from a named committed artefact or an explicit declaration that the method is not measured, never a value inferred from a neighbouring row, and rows compared in one table share one provenance — figures taken under an earlier one may be published only as historical, with that provenance named, because comparing across provenances is precisely what the evaluation capability reports as not comparable. Every limitation a reviewer will meet is declared before they meet it with the measurement that establishes it and the path that would close it, an alert the environment raises about a capability it cannot feed is explained in the demonstration material before the surface that shows it is reached and with the reason it does not apply rather than a request to disregard it, and the script states for each segment the account it is entered with, the exact query typed and what must appear — using, where a behaviour is reachable only under one form of input, that form, and saying why. A validation needing a browser, a credential outside the repository or any other surface the authoring session cannot reach is declared as contributed by whoever performed it with its date and never recorded as observed, kept apart from the datum behind it when that datum is independently verifiable, because a figure being zero and a screen not drawing a line are different claims. The delivery tag and branch are proposed by name and commit and created only on explicit confirmation, and a proposed name that disagrees with what a frozen section declares is reported rather than resolved by editing that section.

## Requirements
### Requirement: Every count of archived changes is published with the unit it counted and the exceptions it applied

The delivery package SHALL publish every count of archived changes together with the unit it counted, and the canonical unit MUST be one directory of `openspec/changes/archive/` because that is the only figure a reader reproduces in a single command without reading the plan; a count in any other unit — fichas of the project plan being the one the existing documentation uses — MUST be labelled with that unit and stated beside the directory count rather than in place of it, and the difference between two units MUST be explained by naming the entries that account for it.

A criterion that classifies by date MUST name every exception it applies rather than leave it to a reader who would apply the rule and arrive at a different figure. `2026-08-03-barcode-qr-scanning` is such an exception: it carries the first date of the AI final project and belongs to the MVP by content — it is counter barcode and QR scanning, its live capability is `barcode-scanning` and it has no ficha in the project plan.

Duplicate directories MUST be declared rather than removed or silently deduplicated. Rearranging the historical archive so that a total adds up is the opposite of making a figure verifiable.

#### Scenario: A published count states its unit

- **WHEN** the delivery package states how many changes were archived for the AI final project
- **THEN** it states whether the figure counts directories of `openspec/changes/archive/` or fichas of the plan
- **AND** it states the command or the document by which a reader reproduces it

#### Scenario: Two units disagree and the difference is named

- **GIVEN** the directory count and the ficha count of the same population differ
- **WHEN** both are published
- **THEN** the entries that account for the difference are named individually
- **AND** neither figure is presented as a correction of the other

#### Scenario: A date rule carries a named exception

- **GIVEN** the boundary between the MVP and the AI final project is expressed as a date
- **WHEN** an archived change falls on the project side by date and on the MVP side by content
- **THEN** it is named explicitly as an exception to the date rule
- **AND** the reason it is classified by content is stated

#### Scenario: Duplicate directories are declared, not removed

- **GIVEN** the archive holds more directories than distinct change slugs
- **WHEN** the totals are published
- **THEN** the duplicate slugs are named and the side of the boundary they fall on is stated
- **AND** no directory is deleted, renamed or merged to make a total add up

### Requirement: Every row of the search-method taxonomy carries a measured figure with its provenance, or is declared unmeasured

The delivery package SHALL publish the taxonomy of search methods with one row per method, and every row MUST carry either a figure taken from a committed measurement artefact named in the row, or an explicit declaration that the method is not measured; a row MUST NOT be filled by analogy with a neighbouring method, by an estimate, or by a figure whose artefact cannot be named.

Rows compared against one another in the same table MUST share one provenance — one golden set version, one run family — and the table MUST declare that provenance. Figures taken under an earlier provenance MAY be published, and then MUST be labelled historical with their own provenance named, never mixed into a comparison with figures taken under another.

#### Scenario: A row cites the artefact its figure comes from

- **WHEN** the taxonomy publishes a figure for a search method
- **THEN** the row names the committed artefact or report the figure was read from

#### Scenario: A method with no measurement is declared unmeasured

- **GIVEN** a search method for which no measurement exists
- **WHEN** its row is published
- **THEN** the row declares the method not measured
- **AND** the row carries no figure inferred from another method

#### Scenario: A comparison does not mix provenances

- **GIVEN** two configurations measured under different golden set versions
- **WHEN** they appear in the same comparison
- **THEN** the comparison is not published as a like-for-like delta
- **AND** the figure taken under the earlier provenance is labelled historical with that provenance named

### Requirement: The frozen sections of the delivery README are reported with their proposed text and never edited

Because the delivery README's structure is fixed by the submission template, the sections the template owns SHALL be treated as frozen: `## 0. Ficha del proyecto`, `### 1.1`, `### 1.2`, `### 1.3`, `## 5. Historias de usuario` and `## 6. Tickets de trabajo`. A change that finds one of them outdated MUST report it with the exact text it proposes and the consequence of leaving it as it is, and MUST NOT apply the edit without the express approval of whoever answers for the delivery.

Editing an editable section that changes a heading MUST update the `## Índice` of the header in the same change, because an index pointing at a heading that no longer exists is a broken deliverable rather than a stale note.

#### Scenario: A frozen section is outdated

- **GIVEN** a frozen section of the delivery README states something the system has since outgrown
- **WHEN** the change that found it is written
- **THEN** the finding is reported with the exact proposed replacement text
- **AND** the section itself is left unmodified

#### Scenario: An editable section changes a heading

- **WHEN** a change renames, adds or removes a heading in an editable section
- **THEN** the `## Índice` of the README header is updated in the same change

### Requirement: Every limitation a reviewer will meet is declared before they meet it, with its closing path

The delivery package SHALL declare every limitation a reviewer is going to encounter in the deployed environment, each with the measurement that establishes it and the path that would close it, and a limitation whose fix is out of scope MUST be declared rather than hidden, worked around on screen, or left to be discovered.

An alert the environment raises that does not apply to what is being evaluated MUST be explained in the demonstration material **before** the surface that shows it is reached, and the explanation MUST say why it does not apply rather than ask the reviewer to disregard it.

#### Scenario: An alert that does not apply is explained in advance

- **GIVEN** the administrator panel raises an alert about a capability the environment cannot feed
- **WHEN** the demonstration material reaches that panel
- **THEN** the alert has already been explained, with the reason it does not apply
- **AND** the explanation states which phase of the work the capability belongs to

#### Scenario: A measured limitation carries its closing path

- **GIVEN** a limitation established by a measurement against the deployed environment
- **WHEN** it is declared in the delivery package
- **THEN** the declaration carries the measurement and the change that would close it
- **AND** it is not presented as intended behaviour

### Requirement: The demonstration script names things the way the measured behaviour requires

The demonstration script SHALL, for each segment, state the account it is entered with, the exact query that is typed, and what must appear, and where a behaviour is reachable only under one form of input the script MUST use that form and say why; naming a piece by its name rather than by its reference does not reach the agent's pivot to substitutes, so the script uses the reference.

#### Scenario: A segment states its account and its query

- **WHEN** the script describes a segment of the demonstration
- **THEN** it names the account the segment is entered with and the exact query that is typed
- **AND** it states what must appear for the segment to have shown what it claims

#### Scenario: A behaviour reachable only one way is exercised that way

- **GIVEN** a measurement establishes that a behaviour is reached when a piece is named by its reference and not when it is named by its name
- **WHEN** the script exercises that behaviour
- **THEN** it uses the reference
- **AND** it states the limitation that makes the other form fail

### Requirement: A validation that needs a surface the session cannot reach is declared as such and kept apart from the datum behind it

A validation requiring a browser, a credential outside the repository, or any other surface the authoring session cannot reach SHALL be declared as contributed by whoever performed it, with the date, and MUST NOT be reported as observed; where the datum behind that validation can be verified independently, the two MUST be published as separate statements, because a figure being zero and a screen not drawing a line are different claims.

#### Scenario: A visual check cannot be performed

- **GIVEN** a validation requires a browser the authoring session does not have
- **WHEN** the evidence is written
- **THEN** the validation is declared as contributed by the responsible party, with its date
- **AND** it is not recorded as observed by the session

#### Scenario: The datum is verifiable and the rendering is not

- **GIVEN** the figure a screen renders can be read from an API and the rendering cannot be seen
- **WHEN** both are reported
- **THEN** the verified figure and the declared rendering are two separate statements

### Requirement: The delivery tag and branch are proposed and created only on confirmation

The delivery tag and the delivery branch SHALL be proposed by name and by commit, and MUST NOT be created or pushed without the express confirmation of whoever answers for the delivery; where the proposed name disagrees with what a frozen section of the README declares, the disagreement MUST be reported rather than resolved by editing that section.

#### Scenario: The tag is proposed

- **WHEN** the change that finalises the delivery is completed
- **THEN** the tag name and the commit it would point at are proposed
- **AND** neither the tag nor the delivery branch is created or pushed

#### Scenario: The proposed name disagrees with the project ficha

- **GIVEN** the proposed tag carries initials that differ from those the frozen project ficha declares
- **WHEN** the proposal is written
- **THEN** the disagreement is reported with both readings
- **AND** the frozen section is left unmodified

