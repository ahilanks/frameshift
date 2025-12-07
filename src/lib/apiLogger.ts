// API Call Logging System for Veo 3.1 verification

export interface ApiCallLog {
  timestamp: string;
  service: 'veo-3.1' | 'grok';
  model: string;
  requestId: string;
  prompt: string;
  status: 'started' | 'success' | 'error';
  duration?: number;
  response?: any;
  error?: string;
  metadata: Record<string, any>;
}

class ApiLogger {
  private logs: ApiCallLog[] = [];

  logVeoCall(data: {
    model: string;
    prompt: string;
    requestId: string;
    metadata: Record<string, any>;
  }): string {
    const log: ApiCallLog = {
      timestamp: new Date().toISOString(),
      service: 'veo-3.1',
      model: data.model,
      requestId: data.requestId,
      prompt: data.prompt,
      status: 'started',
      metadata: data.metadata
    };

    this.logs.push(log);

    // Console logging with clear formatting
    console.log('\n🔥 ===== VEO 3.1 API CALL INITIATED =====');
    console.log(`📅 Timestamp: ${log.timestamp}`);
    console.log(`🤖 Model: ${log.model}`);
    console.log(`🎯 Request ID: ${log.requestId}`);
    console.log(`📝 Prompt Preview: ${log.prompt.substring(0, 200)}...`);
    console.log(`📊 Metadata:`, log.metadata);
    console.log('============================================\n');

    return log.requestId;
  }

  logVeoResponse(requestId: string, response: any, duration: number) {
    const logIndex = this.logs.findIndex(log => log.requestId === requestId);
    if (logIndex !== -1) {
      this.logs[logIndex].status = 'success';
      this.logs[logIndex].response = response;
      this.logs[logIndex].duration = duration;

      console.log('\n✅ ===== VEO 3.1 API RESPONSE RECEIVED =====');
      console.log(`🎯 Request ID: ${requestId}`);
      console.log(`⏱️ Duration: ${duration}ms`);
      console.log(`📦 Response Type:`, typeof response);
      console.log(`🔍 Response Structure:`, {
        hasCandidates: !!response.candidates,
        candidatesCount: response.candidates?.length || 0,
        hasVideoUrl: this.hasVideoUrl(response)
      });
      console.log('===========================================\n');
    }
  }

  logVeoError(requestId: string, error: any, duration?: number) {
    const logIndex = this.logs.findIndex(log => log.requestId === requestId);
    if (logIndex !== -1) {
      this.logs[logIndex].status = 'error';
      this.logs[logIndex].error = error instanceof Error ? error.message : String(error);
      this.logs[logIndex].duration = duration;

      console.log('\n❌ ===== VEO 3.1 API ERROR =====');
      console.log(`🎯 Request ID: ${requestId}`);
      console.log(`⏱️ Duration: ${duration || 0}ms`);
      console.log(`🚨 Error:`, error);
      console.log('==============================\n');
    }
  }

  private hasVideoUrl(response: any): boolean {
    return !!(
      response?.candidates?.[0]?.content?.parts?.[0]?.videoUrl ||
      response?.candidates?.[0]?.content?.parts?.[0]?.video_url ||
      response?.candidates?.[0]?.videoUrl ||
      response?.videoUrl
    );
  }

  getVeoLogs(): ApiCallLog[] {
    return this.logs.filter(log => log.service === 'veo-3.1');
  }

  getStats() {
    const veoLogs = this.getVeoLogs();
    return {
      totalCalls: veoLogs.length,
      successful: veoLogs.filter(log => log.status === 'success').length,
      failed: veoLogs.filter(log => log.status === 'error').length,
      pending: veoLogs.filter(log => log.status === 'started').length,
      averageDuration: veoLogs
        .filter(log => log.duration)
        .reduce((acc, log) => acc + (log.duration || 0), 0) /
        veoLogs.filter(log => log.duration).length || 0
    };
  }

  printSummary() {
    const stats = this.getStats();
    console.log('\n📊 ===== VEO 3.1 API CALL SUMMARY =====');
    console.log(`🔢 Total Calls: ${stats.totalCalls}`);
    console.log(`✅ Successful: ${stats.successful}`);
    console.log(`❌ Failed: ${stats.failed}`);
    console.log(`⏳ Pending: ${stats.pending}`);
    console.log(`⚡ Average Duration: ${stats.averageDuration.toFixed(2)}ms`);
    console.log('====================================\n');
  }
}

export const apiLogger = new ApiLogger();