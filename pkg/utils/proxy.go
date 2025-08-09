package utils

import (
	"bufio"
	"fmt"
	"os"
)

// LoadProxiesFromFile reads a list of proxies from a file.
// Each line in the file should be a proxy URL (e.g., http://user:pass@host:port).
func LoadProxiesFromFile(filename string) ([]string, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("could not open proxy file '%s': %w", filename, err)
	}
	defer file.Close()

	var proxies []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if line != "" {
			proxies = append(proxies, line)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading proxy file: %w", err)
	}

	if len(proxies) == 0 {
		return nil, fmt.Errorf("no proxies found in file '%s'", filename)
	}

	return proxies, nil
}
