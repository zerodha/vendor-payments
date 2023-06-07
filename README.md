<a href="https://zerodha.tech"><img src="https://zerodha.tech/static/images/github-badge.svg" align="right" /></a>

## Introduction

Vendor Payments

## Pointers

1. Complete documentation on how to use this project for vendor payments in any system -
   https://docs.google.com/document/d/1eNaYqmvu12SJdzLAIWILIjc8viYk0JMDhI0RJtrOlGo/

2. If you face errors like `Reference No and Reference Date is mandatory for Bank transaction`

   update payment mode of all 'Accounts' to cash (Except for payable account types)

3. Set financial year in `Fiscal Year` doctype

## Roles needed

R- Read, C- create, W- write(update), S- Submit

Role -> Purchase Invoice, Purchase Order doctypes

1. Accounts User -> R, C, W, S
   (the one who creates purchase invoice or order)
2. Invoice Approver -> R, W
   (the one who approves)
3. Payout -> R, W
   (the one who downloads the report)
4. Accounts Manager -> R, W
   (the one who uploads reconciliation file)
5. Invoice Viewer -> R
6. Invoice Auditor -> R, W
   (first level auditor)
7. Auditor Manager -> R, W
   (second level auditor)


## Data to be created

1. Accounts

For every company present create tds, igst, cgst, sgst accounts

e.g - `IGST - ZSec`, `CGST - ZSec`, `SGST - ZSec`, `TDS - ZSec`, `GST - Credit`

2. Data in `Tax Withholding Category` doctype list should be updated (These are different types of TDS)

like below

## Reminder cron

To send reminder emails after x days of workflow updates
call via cron or some scheduler

`bench execute vendor_payments.vendor_payments.reminders.payments_reminder`

## Contributors

- [Nikhil Ponnuru](https://github.com/nikhilponnuru)

## LICENSE

[LICENSE](./LICENSE)