#!/bin/bash

pgbench -U bench -p 5433 -c 3 bench -T 3600 -f balancecheck1.bench -f balancecheck2.bench -f balancecheck3.bench -f transfer1.bench -f deposit.bench -f withdrawal.bench -f branchreport.bench
