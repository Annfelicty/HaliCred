/**
 * Custom testing utilities for HaliCred frontend components.
 * Provides enhanced render function with providers and custom queries.
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock auth context
interface MockAuthContextType {
  user: any;
  token: string | null;
  login: jest.Mock;
  logout: jest.Mock;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const mockAuthContext: MockAuthContextType = {
  user: {
    id: '1',
    phone: '+254700000001',
    email: 'test@example.com',
    name: 'John Doe',
    business_name: 'Doe Enterprises',
    business_type: 'farmer',
    location: 'Nairobi',
  },
  token: 'mock_token',
  login: jest.fn(),
  logout: jest.fn(),
  isLoading: false,
  isAuthenticated: true,
};

// Create a custom context for testing
const TestAuthContext = React.createContext<MockAuthContextType>(mockAuthContext);

// Custom providers wrapper
interface AllTheProvidersProps {
  children: React.ReactNode;
  authContext?: Partial<MockAuthContextType>;
  queryClient?: QueryClient;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({
  children,
  authContext = {},
  queryClient,
}) => {
  const testQueryClient =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: 0,
          cacheTime: 0,
        },
      },
    });

  const contextValue = { ...mockAuthContext, ...authContext };

  return (
    <BrowserRouter>
      <QueryClientProvider client={testQueryClient}>
        <TestAuthContext.Provider value={contextValue}>
          {children}
        </TestAuthContext.Provider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authContext?: Partial<MockAuthContextType>;
  queryClient?: QueryClient;
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { authContext, queryClient, ...renderOptions } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders authContext={authContext} queryClient={queryClient}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  });
};

// Helper function to create authenticated user context
export const createAuthenticatedUser = (overrides = {}) => ({
  ...mockAuthContext.user,
  ...overrides,
});

// Helper function to create unauthenticated context
export const createUnauthenticatedContext = (): Partial<MockAuthContextType> => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
});

// Helper function to create loading context
export const createLoadingContext = (): Partial<MockAuthContextType> => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
});

// Helper function to wait for async operations
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

// Mock implementations for common hooks
export const mockUseAuth = (overrides: Partial<MockAuthContextType> = {}) => {
  return {
    ...mockAuthContext,
    ...overrides,
  };
};

export const mockUseGreenScore = (overrides = {}) => ({
  data: {
    overall_score: 75,
    energy_efficiency: 80,
    water_conservation: 70,
    waste_management: 85,
    renewable_energy: 65,
    carbon_footprint: 72,
    confidence_score: 0.85,
    evidence_count: 5,
    recommendations: [],
    ...overrides,
  },
  isLoading: false,
  error: null,
  refetch: jest.fn(),
});

export const mockUseLoans = (overrides = {}) => ({
  data: [
    {
      id: '1',
      amount: 500000,
      term: 12,
      purpose: 'equipment',
      status: 'pending',
      interest_rate: 12.5,
      monthly_payment: 44471.0,
      application_date: '2024-01-01T00:00:00Z',
      ...overrides,
    },
  ],
  isLoading: false,
  error: null,
  refetch: jest.fn(),
});

// Form testing utilities
export const fillForm = async (
  getByLabelText: any,
  userEvent: any,
  formData: Record<string, string>
) => {
  for (const [label, value] of Object.entries(formData)) {
    const input = getByLabelText(new RegExp(label, 'i'));
    await userEvent.clear(input);
    await userEvent.type(input, value);
  }
};

export const submitForm = async (getByRole: any, userEvent: any) => {
  const submitButton = getByRole('button', { name: /submit|apply|save/i });
  await userEvent.click(submitButton);
};

// File upload testing utilities
export const createMockFile = (
  name = 'test.jpg',
  size = 1024,
  type = 'image/jpeg'
) => {
  const file = new File(['test content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

export const mockFileUpload = async (
  getByLabelText: any,
  userEvent: any,
  files: File[]
) => {
  const input = getByLabelText(/upload|file|evidence/i);
  await userEvent.upload(input, files);
};

// API response utilities
export const createApiError = (
  status = 500,
  message = 'Internal server error',
  category = 'SYSTEM'
) => ({
  error: {
    category,
    message,
    correlation_id: 'test-correlation-id',
  },
  status,
});

export const createSuccessResponse = (data: any, message = 'Success') => ({
  data,
  message,
  status: 'success',
});

// Component state testing utilities
export const expectLoadingState = (container: HTMLElement) => {
  expect(container).toHaveTextContent(/loading|spinner/i);
};

export const expectErrorState = (container: HTMLElement, errorMessage?: string) => {
  expect(container).toHaveTextContent(/error|failed/i);
  if (errorMessage) {
    expect(container).toHaveTextContent(errorMessage);
  }
};

export const expectEmptyState = (container: HTMLElement) => {
  expect(container).toHaveTextContent(/no data|empty|nothing to show/i);
};

// Accessibility testing utilities
export const checkAccessibility = (element: HTMLElement) => {
  // Check for proper ARIA labels
  const interactiveElements = element.querySelectorAll(
    'button, input, select, textarea, [role="button"], [role="link"]'
  );

  interactiveElements.forEach((el) => {
    const hasLabel =
      el.getAttribute('aria-label') ||
      el.getAttribute('aria-labelledby') ||
      (el as HTMLElement).textContent?.trim();

    expect(hasLabel).toBeTruthy();
  });
};

export const checkKeyboardNavigation = async (
  container: HTMLElement,
  userEvent: any
) => {
  const focusableElements = container.querySelectorAll(
    'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length > 0) {
    const firstElement = focusableElements[0] as HTMLElement;
    firstElement.focus();
    expect(firstElement).toHaveFocus();

    // Test Tab navigation
    await userEvent.tab();
    if (focusableElements.length > 1) {
      expect(focusableElements[1]).toHaveFocus();
    }
  }
};

// Performance testing utilities
export const measureRenderTime = (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

export const expectFastRender = (renderTime: number, maxTime = 100) => {
  expect(renderTime).toBeLessThan(maxTime);
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';

// Override render with our custom version
export { customRender as render };