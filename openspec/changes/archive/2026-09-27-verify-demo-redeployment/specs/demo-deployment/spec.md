## ADDED Requirements

### Requirement: The environment declares its demonstration accounts and what each one exercises

The environment SHALL document, alongside its deployment procedure, every account an evaluator is expected to sign in with, and for each one the point of sale it is bound to and the behaviour that account is the one able to reach. An account list without that second half is insufficient: the operator accounts differ by assortment, and which behaviours are reachable at all depends on which one is used.

This exists because the environment's purpose is to be evaluated by somebody who did not build it. The three operator accounts are bound to points of sale with deliberately different assortments — maximum, minimum, and the highest exposure to stock-outs — so abstention, substitutes, the out-of-stock warnings and the agent's pivot to substitutes are **reachable from one account and not from another**. An evaluator given a URL and a single credential can correctly conclude that a behaviour does not exist when it is merely out of reach.

The documentation MUST also state the known restriction that governs one of those behaviours: the agent's pivot to substitutes is unreachable when a piece is named by its product name instead of its reference, because the catalogue tool's observation does not carry the name. Omitting that turns a declared limitation into an apparent defect.

Credentials seeded by the application MUST be documented as they are, and MUST NOT be rotated for presentation: rotating them would move a seeded entity for a cosmetic reason and add a secret to an inventory the parameter store keeps deliberately short. A seeded account whose password is a constant of a public repository MUST be documented as deactivated rather than quietly omitted, because an evaluator who finds it refused needs to know that the refusal is deliberate; and the documentation MUST NOT present a password that no longer signs in as though it did, which is how the administrator credentials of this environment were described until 2026-09-27.

#### Scenario: Every demonstration account is documented with its scope and its purpose

- **WHEN** the deployment documentation is read
- **THEN** each account an evaluator signs in with is named
- **AND** each one states the point of sale it is bound to
- **AND** each one states the behaviour it is the account able to reach

#### Scenario: The seeded administrator account is documented as deliberately unusable

- **GIVEN** an account the application's seeder recreates on every start with a password that is a constant of a public repository
- **WHEN** the deployment documentation is read
- **THEN** that account is documented as present and deactivated rather than omitted
- **AND** the documentation states that a refused sign-in is the environment working and not a fault
- **AND** it states that the account must stay deactivated, and why

#### Scenario: The usable administrator account is documented without its password

- **WHEN** the deployment documentation is read
- **THEN** the administrator account an evaluator would actually use is named
- **AND** its password is stated to be deliberately absent from the repository, with how to reset it
- **AND** it is not held in the parameter store
- **AND** the documentation says which administrator-only surface it reaches

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
