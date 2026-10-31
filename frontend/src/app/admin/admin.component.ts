
import {
  Component,
  OnInit,
  OnDestroy,
  AfterViewInit,
  ElementRef,
  ViewChild,
  ChangeDetectorRef
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import Chart from 'chart.js/auto';

// Dashboard statistics returned by the backend
interface AdminStatistics {
  total_transactions: number;
  completed_transactions: number;
  fraud_transactions: number;
  high_risk_transactions: number;
  total_transaction_amount: number;
  average_fraud_score: number;
}

// Fraud transaction returned by the backend
interface FraudTransaction {
  transaction_id: number;
  amount: number;
  fraud_score: number;
  risk_level?: string;
  status: string;
  created_at?: string;
}

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive
  ],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent
  implements OnInit, AfterViewInit, OnDestroy {

  private readonly apiUrl = 'http://127.0.0.1:8000';

  statistics: AdminStatistics | null = null;
  fraudTransactions: FraudTransaction[] = [];

  loading = false;
  error = '';

  private viewReady = false;
  private transactionChart: Chart | null = null;
  private riskChart: Chart | null = null;

  @ViewChild('transactionChart')
  transactionChartRef?: ElementRef<HTMLCanvasElement>;

  @ViewChild('riskChart')
  riskChartRef?: ElementRef<HTMLCanvasElement>;

  constructor(
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.renderCharts();
  }

  ngOnDestroy(): void {
    this.destroyCharts();
  }

  // Authentication headers
  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');

    return new HttpHeaders({
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    });
  }

  // Load statistics and fraud records from FastAPI
  loadDashboard(): void {
    this.loading = true;
    this.error = '';

    this.http
      .get<AdminStatistics>(
        `${this.apiUrl}/transactions/statistics`,
        { headers: this.getHeaders() }
      )
      .subscribe({
        next: (data) => {
          this.statistics = data;
          this.loading = false;

          // Update the DOM before accessing canvas elements
          this.cdr.detectChanges();
          this.renderCharts();
        },
        error: (err) => {
          console.error('Statistics API error:', err);

          this.loading = false;
          this.error =
            'Unable to load dashboard statistics. Please check the backend and login again.';

          this.cdr.detectChanges();
        }
      });

    this.loadFraudTransactions();
  }

  // Load fraud-monitoring records
  private loadFraudTransactions(): void {
    this.http
      .get<FraudTransaction[]>(
        `${this.apiUrl}/admin/fraud-transactions`,
        { headers: this.getHeaders() }
      )
      .subscribe({
        next: (response) => {
          // Support either a direct array or a wrapped response.
          const result = response as unknown;

          if (Array.isArray(result)) {
            this.fraudTransactions = result as FraudTransaction[];
          } else if (
            result !== null &&
            typeof result === 'object' &&
            'fraud_transactions' in result &&
            Array.isArray(
              (result as { fraud_transactions: unknown })
                .fraud_transactions
            )
          ) {
            this.fraudTransactions =
              (result as { fraud_transactions: FraudTransaction[] })
                .fraud_transactions;
          } else if (
            result !== null &&
            typeof result === 'object' &&
            'transactions' in result &&
            Array.isArray(
              (result as { transactions: unknown }).transactions
            )
          ) {
            this.fraudTransactions =
              (result as { transactions: FraudTransaction[] })
                .transactions;
          } else {
            this.fraudTransactions = [];
          }

          this.cdr.detectChanges();
        },
        error: (err) => {
          console.error('Fraud transactions API error:', err);
          this.fraudTransactions = [];
          this.cdr.detectChanges();
        }
      });
  }

  // Draw or update both charts
  private renderCharts(): void {
    if (
      !this.viewReady ||
      !this.statistics ||
      !this.transactionChartRef?.nativeElement ||
      !this.riskChartRef?.nativeElement
    ) {
      return;
    }

    this.destroyCharts();

    const stats = this.statistics;

    const total = Number(stats.total_transactions) || 0;
    const completed = Number(stats.completed_transactions) || 0;
    const fraud = Number(stats.fraud_transactions) || 0;
    const highRisk = Number(stats.high_risk_transactions) || 0;

    const otherTransactions = Math.max(total - completed, 0);

    // Doughnut chart: completed versus other transactions
    this.transactionChart = new Chart(
      this.transactionChartRef.nativeElement,
      {
        type: 'doughnut',
        data: {
          labels: [
            'Completed',
            'Other transactions'
          ],
          datasets: [
            {
              data: [completed, otherTransactions],
              backgroundColor: [
                '#16a34a',
                '#dbeafe'
              ],
              borderColor: '#ffffff',
              borderWidth: 3,
              hoverOffset: 8
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '68%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 20,
                usePointStyle: true
              }
            },
            tooltip: {
              enabled: true
            }
          }
        }
      }
    );

    // Bar chart: overall transaction and risk indicators
    this.riskChart = new Chart(
      this.riskChartRef.nativeElement,
      {
        type: 'bar',
        data: {
          labels: [
            'Total',
            'Completed',
            'Fraud',
            'High risk'
          ],
          datasets: [
            {
              label: 'Transactions',
              data: [
                total,
                completed,
                fraud,
                highRisk
              ],
              backgroundColor: [
                '#2563eb',
                '#16a34a',
                '#dc2626',
                '#f59e0b'
              ],
              borderRadius: 7,
              maxBarThickness: 55
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0
              },
              grid: {
                color: '#edf1f7'
              }
            },
            x: {
              grid: {
                display: false
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: true
            }
          }
        }
      }
    );
  }

  // Clean up old chart instances before recreating them
  private destroyCharts(): void {
    if (this.transactionChart) {
      this.transactionChart.destroy();
      this.transactionChart = null;
    }

    if (this.riskChart) {
      this.riskChart.destroy();
      this.riskChart = null;
    }
  }

  // Format amounts in Indian Rupees
  formatCurrency(amount: number | null | undefined): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(Number(amount) || 0);
  }

  // Logout and return to the home/login page
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('role');

    this.destroyCharts();

    this.router.navigate(['/']);
  }
}
