## ADDED Requirements

### Requirement: The environment declares its demonstration accounts and what each one exercises

The environment SHALL document, alongside its deployment procedure, every account an evaluator is expected to sign in with, and for each one the point of sale it is bound to and the behaviour that account is the one able to reach. An account list without that second half is insufficient: the operator accounts differ by assortment, and which behaviours are reachable at all depends on which one is used.

This exists because the environment's purpose is to be evaluated by somebody who did not build it. The three operator accounts are bound to points of sale with deliberately different assortments — maximum, minimum, and the highest exposure to stock-outs — so abstention, substitutes, the out-of-stock warnings and the agent's pivot to substitutes are **reachable from one account and not from another**. An evaluator given a URL and a single credential can correctly conclude that a behaviour does not exist when it is merely out of reach.

The documentation MUST also state the known restriction that governs one of those behaviours: the agent's pivot to substitutes is unreachable when a piece is named by its product name instead of its reference, because the catalogue tool's observation does not carry the name. Omitting that turns a declared limitation into an apparent defect.

Credentials seeded by the application MUST be documented as they are, and MUST NOT be rotated for presentation: rotating them would move a seeded entity for a cosmetic reason and add a secret to an inventory the parameter store keeps deliberately short.

#### Scenario: Every demonstration account is documented with its scope and its purpose

- **WHEN** the deployment documentation is read
- **THEN** each account an evaluator signs in with is named
- **AND** each one states the point of sale it is bound to
- **AND** each one states the behaviour it is the account able to reach

#### Scenario: The administrator account is documented as seeded

- **WHEN** the deployment documentation is read
- **THEN** the administrator credentials are stated as the application seeds them
- **AND** they are not held in the parameter store
- **AND** the documentation says which administrator-only surface they reach

#### Scenario: A behaviour reachable from only one account says so

- **GIVEN** a behaviour that depends on the assortment of a point of sale
- **WHEN** the deployment documentation lists the accounts
- **THEN** it names the account from which that behaviour is reachable
- **AND** an evaluator following it does not have to discover the dependency by trial

#### Scenario: The known restriction of the agent's pivot is stated

- **WHEN** the deployment documentation describes how to exercise the agent
- **THEN** it states that the piece must be named by its reference
- **AND** it states that naming it by its product name leaves the pivot unreachable
- **AND** it presents that as a declared limitation rather than as a fault of the environment
