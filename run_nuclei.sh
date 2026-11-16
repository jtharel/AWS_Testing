#!/bin/bash
echo "Starting nuclei scan at $(date)"
nuclei -l IPs.txt -o nuclei_results.txt -stats
echo ""
echo "Scan completed at $(date)"
echo "Results saved to nuclei_results.txt"
