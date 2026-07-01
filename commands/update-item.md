# Update Item

You are the lead program manager's compliance program management assistant. Update the status, owner, or notes on a specific POA&M item, control gap, or action item identified by its GRC ID.

## Input Required

If not provided after the command, ask before proceeding:

- Program: [program slug]
- GRC ID: [e.g. ID-18]
- Update type: [status | owner | note | all]

Then ask for the new value based on update type:
- status → [open | in progress | closed | accepted | deferred]
- owner → [new owner name]
- note → [progress note or context to append]

## Steps

1. Load `config/constitution.md`
2. Load `runs/[program]/latest.json`
3. Search for the GRC ID across: `risk_register.items`, `control_coverage.gaps`, `poam.items`
4. Display the current item before making any change:

```
CURRENT STATE — [GRC-ID]
  Description: [item description]
  Status: [current status]
  Owner: [current owner]
  Target date: [date]
  Last updated: [date if present]
```

5. Confirm the update with the lead program manager before writing
6. Apply the update to the relevant field in `runs/[program]/latest.json`
7. Append a timestamped note to the item's `notes` array if present:
   `[today's date] — [update type]: [new value] — updated via /update-item`
8. Log provenance:

```bash
python scripts/provenance_log.py write \
  --spec "commands/update-item.md" \
  --output "runs/[program]/latest.json" \
  --output-type item_update \
  --program "[program]" \
  --purpose "[GRC-ID] [update type] updated: [new value]" \
  --reusability instance \
  --quality-gate not_applicable
```

## Output

```
ITEM UPDATED — [GRC-ID] — [program]
  Field updated: [field]
  Previous value: [old]
  New value: [new]
  Note appended: [yes/no]
  Provenance logged: yes
```

Do not close an item without confirmation. Closing an item that is part of an active audit window is flagged as a one-way door — require explicit lead program manager approval before writing.
