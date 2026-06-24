import { useState, useEffect, useCallback } from 'react'
import DataSourceList from './components/DataSourceList'
import type { DataSource } from './components/DataSourceList'
import UploadForm from './components/UploadForm'
import BatchHistory from './components/BatchHistory'
import type { Batch } from './components/BatchHistory'
import { PipelineMonitor } from './components/PipelineMonitor'
import { QualityReport } from './components/QualityReport'
import { Toaster } from "@/components/ui/sonner"
import { LayoutDashboard, Database, Activity, Settings, Menu, ServerCog } from "lucide-react"

function App() {
  const [activeTab, setActiveTab] = useState('ingestion')
  const [sources, setSources] = useState<DataSource[]>([])
  const [loadingSources, setLoadingSources] = useState(true)

  const [batches, setBatches] = useState<Batch[]>([])
  // Change initial loading state to false to avoid initial flashing if there's no data
  const [loadingBatches, setLoadingBatches] = useState(false)
  const [batchError, setBatchError] = useState<string | null>(null)

  const fetchSources = useCallback(() => {
    fetch('http://127.0.0.1:8080/api/v1/sources')
      .then(res => res.json())
      .then(data => {
        setSources(data)
        setLoadingSources(false)
      })
      .catch(err => {
        console.error('获取数据源失败:', err)
        setLoadingSources(false)
      })
  }, [])

  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  const fetchBatches = useCallback((showLoading = false) => {
    if (showLoading) setLoadingBatches(true);
    setBatchError(null)
    fetch('http://127.0.0.1:8080/api/v1/ingestion/batches')
      .then(res => {
        if (!res.ok) throw new Error('获取批次历史记录失败')
        return res.json()
      })
      .then(data => {
        setBatches(Array.isArray(data) ? data : [])
        setLoadingBatches(false)
      })
      .catch(err => {
        setBatchError(err.message)
        setLoadingBatches(false)
      })
  }, [])

  useEffect(() => {
    fetchBatches(true)
  }, [fetchBatches])

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-50 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-slate-800">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-400" />
            OMOP 数据平台
          </h2>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <button 
            onClick={() => setActiveTab('ingestion')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'ingestion' ? 'bg-blue-600/20 text-blue-400' : 'hover:bg-slate-800 text-slate-300'}`}
          >
            <LayoutDashboard className="w-5 h-5" />
            数据接入工作台
          </button>
          <button 
            onClick={() => setActiveTab('pipeline')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'pipeline' ? 'bg-blue-600/20 text-blue-400' : 'hover:bg-slate-800 text-slate-300'}`}
          >
            <ServerCog className="w-5 h-5" />
            数据清洗与归一化
          </button>
          <button 
            onClick={() => setActiveTab('quality')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'quality' ? 'bg-blue-600/20 text-blue-400' : 'hover:bg-slate-800 text-slate-300'}`}
          >
            <Activity className="w-5 h-5" />
            质量评估报告
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'settings' ? 'bg-blue-600/20 text-blue-400' : 'hover:bg-slate-800 text-slate-300'}`}
          >
            <Settings className="w-5 h-5" />
            系统配置管理
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b flex items-center px-6 justify-between shrink-0">
          <div className="flex items-center gap-4">
            <button className="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg">
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold text-slate-800">
              {activeTab === 'ingestion' && '数据接入工作台'}
              {activeTab === 'pipeline' && '数据清洗与归一化管线'}
              {activeTab === 'quality' && '质量评估报告'}
              {activeTab === 'settings' && '系统配置管理'}
            </h1>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span>MVP 1.0</span>
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
              管
            </div>
          </div>
        </header>

        {/* Content Scroll Area */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-6xl mx-auto space-y-6">
            {activeTab === 'ingestion' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Data Sources */}
                <div className="lg:col-span-1">
                  <DataSourceList initialData={sources} isLoading={loadingSources} onSourceAdded={fetchSources} />
                </div>
                
                {/* Right Column: Upload & History */}
                <div className="lg:col-span-2 space-y-6">
                  <UploadForm onUploadSuccess={fetchBatches} />
                  <BatchHistory batches={batches} loading={loadingBatches} error={batchError} onRefresh={fetchBatches} />
                </div>
              </div>
            )}
            
            {activeTab === 'pipeline' && (
              <PipelineMonitor />
            )}

            {activeTab === 'quality' && (
              <QualityReport />
            )}

            {activeTab === 'settings' && (
              <div className="bg-white p-8 rounded-xl border text-center text-slate-500">
                系统配置管理模块开发中...
              </div>
            )}
          </div>
        </div>
      </main>
      <Toaster />
    </div>
  )
}

export default App
