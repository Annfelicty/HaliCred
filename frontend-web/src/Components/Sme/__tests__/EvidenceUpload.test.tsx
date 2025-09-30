/**
 * Comprehensive tests for EvidenceUpload component.
 * Tests file upload functionality, validation, progress tracking, and accessibility.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import {
  createMockFile,
  mockFileUpload,
  createApiError,
  checkAccessibility,
  expectLoadingState,
  expectErrorState,
} from '../../../test/utils/test-utils';
import EvidenceUpload from '../EvidenceUpload';

// Mock the API calls
jest.mock('../../../lib/api');
const mockApi = require('../../../lib/api');

describe('EvidenceUpload', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, cacheTime: 0 },
      },
    });

    jest.clearAllMocks();

    // Mock successful upload by default
    mockApi.uploadEvidence = jest.fn().mockResolvedValue({
      evidence_id: '1',
      status: 'uploaded',
      message: 'Evidence uploaded successfully',
    });
  });

  describe('File Selection', () => {
    it('renders file upload interface', () => {
      render(<EvidenceUpload />, { queryClient });

      expect(screen.getByLabelText(/select file|upload evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/drag and drop|choose file/i)).toBeInTheDocument();
    });

    it('accepts valid image files', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('solar-panel.jpg', 1024 * 500, 'image/jpeg');
      const input = screen.getByLabelText(/upload|file/i);

      await user.upload(input, file);

      expect(screen.getByText('solar-panel.jpg')).toBeInTheDocument();
      expect(screen.getByText(/500 KB/)).toBeInTheDocument();
    });

    it('accepts valid document files', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('invoice.pdf', 1024 * 200, 'application/pdf');
      const input = screen.getByLabelText(/upload|file/i);

      await user.upload(input, file);

      expect(screen.getByText('invoice.pdf')).toBeInTheDocument();
      expect(screen.getByText(/200 KB/)).toBeInTheDocument();
    });

    it('handles multiple file selection', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const files = [
        createMockFile('receipt1.jpg', 1024 * 100, 'image/jpeg'),
        createMockFile('receipt2.jpg', 1024 * 150, 'image/jpeg'),
      ];

      const input = screen.getByLabelText(/upload|file/i);
      await user.upload(input, files);

      expect(screen.getByText('receipt1.jpg')).toBeInTheDocument();
      expect(screen.getByText('receipt2.jpg')).toBeInTheDocument();
    });

    it('supports drag and drop functionality', async () => {
      render(<EvidenceUpload />, { queryClient });

      const dropzone = screen.getByTestId('file-dropzone');
      const file = createMockFile('dragged-file.jpg', 1024 * 300, 'image/jpeg');

      // Simulate drag and drop
      fireEvent.dragEnter(dropzone);
      fireEvent.dragOver(dropzone);
      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(screen.getByText('dragged-file.jpg')).toBeInTheDocument();
      });
    });
  });

  describe('File Validation', () => {
    it('rejects files that are too large', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const largeFile = createMockFile('large-file.jpg', 1024 * 1024 * 11, 'image/jpeg'); // 11MB
      const input = screen.getByLabelText(/upload|file/i);

      await user.upload(input, largeFile);

      expect(screen.getByText(/file size too large|exceeds maximum size/i)).toBeInTheDocument();
    });

    it('rejects unsupported file types', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const unsupportedFile = createMockFile('document.exe', 1024 * 100, 'application/x-executable');
      const input = screen.getByLabelText(/upload|file/i);

      await user.upload(input, unsupportedFile);

      expect(screen.getByText(/unsupported file type|invalid format/i)).toBeInTheDocument();
    });

    it('validates file name length', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const longFileName = 'a'.repeat(256) + '.jpg';
      const file = createMockFile(longFileName, 1024 * 100, 'image/jpeg');
      const input = screen.getByLabelText(/upload|file/i);

      await user.upload(input, file);

      expect(screen.getByText(/filename too long/i)).toBeInTheDocument();
    });

    it('shows file format requirements', () => {
      render(<EvidenceUpload />, { queryClient });

      expect(screen.getByText(/supported formats|accepted types/i)).toBeInTheDocument();
      expect(screen.getByText(/JPG|JPEG|PNG|PDF/i)).toBeInTheDocument();
      expect(screen.getByText(/maximum.*10.*MB/i)).toBeInTheDocument();
    });
  });

  describe('Evidence Type Selection', () => {
    it('displays evidence type options', () => {
      render(<EvidenceUpload />, { queryClient });

      expect(screen.getByLabelText(/evidence type/i)).toBeInTheDocument();
    });

    it('shows different evidence types', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const select = screen.getByLabelText(/evidence type/i);
      await user.click(select);

      expect(screen.getByText(/solar panel/i)).toBeInTheDocument();
      expect(screen.getByText(/energy bill/i)).toBeInTheDocument();
      expect(screen.getByText(/water conservation/i)).toBeInTheDocument();
      expect(screen.getByText(/waste management/i)).toBeInTheDocument();
    });

    it('requires evidence type selection', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 100, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const submitButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(submitButton);

      expect(screen.getByText(/please select evidence type/i)).toBeInTheDocument();
    });

    it('updates form when evidence type is selected', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const select = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(select, 'solar_panel');

      expect(screen.getByDisplayValue(/solar panel/i)).toBeInTheDocument();
    });
  });

  describe('Upload Process', () => {
    it('uploads file successfully', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      // Select file
      const file = createMockFile('receipt.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      // Select evidence type
      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      // Add description
      const descriptionInput = screen.getByLabelText(/description/i);
      await user.type(descriptionInput, 'Solar panel installation receipt');

      // Submit upload
      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockApi.uploadEvidence).toHaveBeenCalledWith(
          expect.objectContaining({
            file,
            evidence_type: 'solar_panel',
            description: 'Solar panel installation receipt',
          })
        );
      });

      expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
    });

    it('shows upload progress', async () => {
      const user = userEvent.setup();

      // Mock upload with progress
      mockApi.uploadEvidence = jest.fn().mockImplementation(() => {
        return new Promise((resolve) => {
          setTimeout(() => resolve({
            evidence_id: '1',
            status: 'uploaded',
          }), 1000);
        });
      });

      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 500, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      // Check for progress indicator
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText(/uploading|in progress/i)).toBeInTheDocument();
    });

    it('handles upload errors gracefully', async () => {
      const user = userEvent.setup();

      mockApi.uploadEvidence = jest.fn().mockRejectedValue(
        createApiError(500, 'Upload failed', 'SYSTEM')
      );

      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/upload failed|error uploading/i)).toBeInTheDocument();
      });

      // Should show retry button
      expect(screen.getByRole('button', { name: /retry|try again/i })).toBeInTheDocument();
    });

    it('allows retry after failed upload', async () => {
      const user = userEvent.setup();

      mockApi.uploadEvidence = jest.fn()
        .mockRejectedValueOnce(createApiError(500, 'Network error'))
        .mockResolvedValueOnce({ evidence_id: '1', status: 'uploaded' });

      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
      });

      // Retry upload
      const retryButton = screen.getByRole('button', { name: /retry|try again/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
      });

      expect(mockApi.uploadEvidence).toHaveBeenCalledTimes(2);
    });
  });

  describe('Form Validation', () => {
    it('validates required fields before upload', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      expect(screen.getByText(/please select a file/i)).toBeInTheDocument();
    });

    it('validates description length', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const descriptionInput = screen.getByLabelText(/description/i);
      const longDescription = 'a'.repeat(501); // Assuming 500 character limit
      await user.type(descriptionInput, longDescription);

      expect(screen.getByText(/description too long|exceeds maximum length/i)).toBeInTheDocument();
    });

    it('shows field validation errors in real-time', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const descriptionInput = screen.getByLabelText(/description/i);
      await user.type(descriptionInput, 'ab');
      await user.clear(descriptionInput);

      expect(screen.getByText(/description is required/i)).toBeInTheDocument();
    });
  });

  describe('User Experience', () => {
    it('disables upload button during upload', async () => {
      const user = userEvent.setup();

      // Mock slow upload
      mockApi.uploadEvidence = jest.fn().mockImplementation(() =>
        new Promise((resolve) => setTimeout(resolve, 2000))
      );

      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      expect(uploadButton).toBeDisabled();
      expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    });

    it('shows file preview before upload', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('image.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      expect(screen.getByTestId('file-preview')).toBeInTheDocument();
      expect(screen.getByText('image.jpg')).toBeInTheDocument();
    });

    it('allows file removal before upload', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      expect(screen.getByText('test.jpg')).toBeInTheDocument();

      const removeButton = screen.getByRole('button', { name: /remove|delete/i });
      await user.click(removeButton);

      expect(screen.queryByText('test.jpg')).not.toBeInTheDocument();
    });

    it('shows upload success message with next steps', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
        expect(screen.getByText(/processing|being analyzed/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /upload another|view dashboard/i })).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels and structure', () => {
      const { container } = render(<EvidenceUpload />, { queryClient });

      checkAccessibility(container);
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const fileInput = screen.getByLabelText(/upload|file/i);
      fileInput.focus();
      expect(fileInput).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/evidence type/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/description/i)).toHaveFocus();
    });

    it('provides screen reader announcements', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/file selected|1 file ready/i);
    });

    it('has proper ARIA attributes for upload states', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      expect(uploadButton).toHaveAttribute('aria-describedby');

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      await user.click(uploadButton);

      await waitFor(() => {
        expect(uploadButton).toHaveAttribute('aria-busy', 'true');
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles network interruption during upload', async () => {
      const user = userEvent.setup();

      mockApi.uploadEvidence = jest.fn().mockRejectedValue(
        new Error('Network error')
      );

      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/network error|connection lost/i)).toBeInTheDocument();
      });
    });

    it('handles browser file API not available', () => {
      // Mock FileReader not available
      const originalFileReader = window.FileReader;
      delete (window as any).FileReader;

      render(<EvidenceUpload />, { queryClient });

      expect(screen.getByText(/file upload not supported/i)).toBeInTheDocument();

      // Restore FileReader
      window.FileReader = originalFileReader;
    });

    it('prevents duplicate uploads', async () => {
      const user = userEvent.setup();
      render(<EvidenceUpload />, { queryClient });

      const file = createMockFile('test.jpg', 1024 * 200, 'image/jpeg');
      await mockFileUpload(screen.getByLabelText, user, [file]);

      const typeSelect = screen.getByLabelText(/evidence type/i);
      await user.selectOptions(typeSelect, 'solar_panel');

      const uploadButton = screen.getByRole('button', { name: /upload|submit/i });

      // Click multiple times rapidly
      await user.click(uploadButton);
      await user.click(uploadButton);
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockApi.uploadEvidence).toHaveBeenCalledTimes(1);
      });
    });
  });
});