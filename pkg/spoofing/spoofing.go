package spoofing

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/brianvoe/gofakeit/v6"
)

// BrowserProfile holds a consistent set of browser fingerprint data.
type BrowserProfile struct {
	UserAgent      string
	SecChUa        string
	SecChUaMobile  string
	SecChUaPlatform string
	AcceptLanguage string
	Headers        map[string]string
}

var (
	// Regex to find browser and version from a user agent string.
	// Catches Chrome, Firefox, Safari, Edge.
	browserRegex = regexp.MustCompile(`(Chrome|Firefox|Edge|Safari)\/([\d.]+)`)
)

// NewBrowserProfile generates a new, consistent browser profile.
func NewBrowserProfile() *BrowserProfile {
	// Seed gofakeit for better randomness if needed, though it seeds itself.
	// gofakeit.Seed(time.Now().UnixNano())

	ua := gofakeit.UserAgent()
	browser, majorVersion, platform := parseUserAgent(ua)

	profile := &BrowserProfile{
		UserAgent:      ua,
		AcceptLanguage: gofakeit.LanguageAbbreviation() + "-" + gofakeit.CountryAbr(),
	}

	// Generate Sec-CH-UA headers based on the browser
	profile.SecChUaMobile = "?0" // Assume desktop for simplicity for now
	if platform == "Android" || platform == "iPhone" {
		profile.SecChUaMobile = "?1"
	}

	profile.SecChUaPlatform = fmt.Sprintf(`"%s"`, platform)

	switch browser {
	case "Chrome":
		profile.SecChUa = fmt.Sprintf(`"Not/A)Brand";v="99", "Google Chrome";v="%s", "Chromium";v="%s"`, majorVersion, majorVersion)
	case "Edge":
		profile.SecChUa = fmt.Sprintf(`"Not/A)Brand";v="99", "Microsoft Edge";v="%s", "Chromium";v="%s"`, majorVersion, majorVersion)
	case "Firefox":
		// Firefox doesn't typically send Sec-CH-UA headers in the same way, but we can create a plausible one.
		profile.SecChUa = fmt.Sprintf(`"Firefox";v="%s"`, majorVersion)
		profile.SecChUaPlatform = `""` // Often empty for Firefox
	case "Safari":
		// Safari also has a different pattern.
		profile.SecChUa = fmt.Sprintf(`"Safari";v="%s", "AppleWebKit/605.1.15";v="605"`, majorVersion)
	default:
		// Fallback for other user agents
		profile.SecChUa = `"Not/A)Brand";v="99"`
	}

	profile.generateHeaders()
	return profile
}

// parseUserAgent extracts key information from a user agent string.
func parseUserAgent(ua string) (browser, majorVersion, platform string) {
	// Default values
	browser = "Unknown"
	majorVersion = "0"
	platform = "Windows"

	// Determine platform
	if strings.Contains(ua, "Windows") {
		platform = "Windows"
	} else if strings.Contains(ua, "Macintosh") {
		platform = "macOS"
	} else if strings.Contains(ua, "Linux") && !strings.Contains(ua, "Android") {
		platform = "Linux"
	} else if strings.Contains(ua, "Android") {
		platform = "Android"
	} else if strings.Contains(ua, "iPhone") {
		platform = "iOS"
	}

	// Find browser and version
	matches := browserRegex.FindStringSubmatch(ua)
	if len(matches) >= 3 {
		// Avoid picking "Safari" if "Chrome" is also present
		if !(matches[1] == "Safari" && strings.Contains(ua, "Chrome")) {
			browser = matches[1]
			majorVersion = strings.Split(matches[2], ".")[0]
		}
	}

	// A common case where Safari is the rendering engine but Chrome is the browser
	if browser == "Unknown" && strings.Contains(ua, "Chrome") {
		chromeMatches := regexp.MustCompile(`Chrome\/([\d.]+)`).FindStringSubmatch(ua)
		if len(chromeMatches) >= 2 {
			browser = "Chrome"
			majorVersion = strings.Split(chromeMatches[1], ".")[0]
		}
	}

	return
}

// generateHeaders creates the final map of HTTP headers.
func (p *BrowserProfile) generateHeaders() {
	p.Headers = make(map[string]string)
	p.Headers["User-Agent"] = p.UserAgent
	p.Headers["Accept-Language"] = p.AcceptLanguage

	// Add Sec-CH-UA headers only if they are non-empty
	if p.SecChUa != "" {
		p.Headers["sec-ch-ua"] = p.SecChUa
	}
	if p.SecChUaMobile != "" {
		p.Headers["sec-ch-ua-mobile"] = p.SecChUaMobile
	}
	if p.SecChUaPlatform != "" {
		p.Headers["sec-ch-ua-platform"] = p.SecChUaPlatform
	}

	// Add standard request headers
	p.Headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
	p.Headers["Accept-Encoding"] = "gzip, deflate, br"
	p.Headers["Sec-Fetch-Dest"] = "document"
	p.Headers["Sec-Fetch-Mode"] = "navigate"
	p.Headers["Sec-Fetch-Site"] = "none"
	p.Headers["Sec-Fetch-User"] = "?1"
	p.Headers["Upgrade-Insecure-Requests"] = "1"
	p.Headers["Referer"] = fmt.Sprintf("https://www.%s/", gofakeit.DomainName())
}

// GetRandomReferer provides a random referer for attacks that need it.
func GetRandomReferer() string {
	return fmt.Sprintf("https://www.%s/%s", gofakeit.DomainName(), gofakeit.BuzzWord())
}
